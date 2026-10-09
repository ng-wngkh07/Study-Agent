"""Incremental benchmark evaluation script for RAG retrieval and generation.
Saves after every single query to allow seamless resume and fault tolerance.
Captures retrieval trace directly from the agent without redundant searches.
Uses GPU coordinator for all model and embedding operations.
"""

import json
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import BASE_DIR, DEFAULT_CHAT_MODEL, DEFAULT_EMBED_MODEL
from app.rag_agent import PsychologyAgent
from app.gpu_lock import gpu_coordinator

BENCHMARK_QUERIES = [
    {
        "id": "game_theory_overview",
        "domain": "Lý thuyết trò chơi",
        "type": "broad_overview",
        "query": "Các lý thuyết cốt lõi trong lý thuyết trò chơi và ứng dụng của chúng trong tâm lý học là gì?",
        "expected_facets": ["cân bằng Nash", "song đề tù nhân", "trò chơi tổng bằng 0", "hợp tác"]
    },
    {
        "id": "learning_conditioning",
        "domain": "Học tập & Điều kiện hóa",
        "type": "theory_comparison",
        "query": "So sánh điều kiện hóa cổ điển (Pavlov) và điều kiện hóa thao tác (Skinner): nguyên lý và điểm khác biệt cốt lõi?",
        "expected_facets": ["Pavlov", "Skinner", "củng cố", "kích thích"]
    },
    {
        "id": "memory_working",
        "domain": "Trí nhớ",
        "type": "concept_mechanism",
        "query": "Trí nhớ làm việc (working memory) hoạt động như thế nào và có mối liên hệ gì với hồi hải mã và vỏ não trước trán?",
        "expected_facets": ["working memory", "hồi hải mã", "vỏ não trước trán"]
    },
    {
        "id": "personality_theories",
        "domain": "Nhân cách",
        "type": "broad_comparison",
        "query": "Tổng quan về các lý thuyết nhân cách: mô hình năm yếu tố (Big Five) khác gì với quan điểm phân tâm học của Freud?",
        "expected_facets": ["Big Five", "Freud", "vô thức", "đặc điểm tính cách"]
    },
    {
        "id": "cognition_systems",
        "domain": "Nhận thức",
        "type": "concept_mechanism",
        "query": "Hệ thống 1 và Hệ thống 2 trong cuốn Tư duy nhanh và chậm hoạt động như thế nào, khi nào xảy ra sai lệch?",
        "expected_facets": ["Hệ thống 1", "Hệ thống 2", "tự động", "thiên kiến"]
    },
    {
        "id": "emotion_theories",
        "domain": "Cảm xúc",
        "type": "theory_comparison",
        "query": "So sánh các lý thuyết cảm xúc chính (James-Lange, Cannon-Bard và Schachter-Singer) về vai trò của phản ứng sinh lý và đánh giá nhận thức?",
        "expected_facets": ["James-Lange", "Cannon-Bard", "Schachter-Singer", "sinh lý", "nhận thức"]
    },
    {
        "id": "motivation_sdt",
        "domain": "Động cơ",
        "type": "theory_overview",
        "query": "Thuyết tự quyết (Self-Determination Theory) phân chia động lực như thế nào và ba nhu cầu tâm lý cơ bản là gì?",
        "expected_facets": ["nội tại", "ngoại tại", "tự chủ", "năng lực", "gắn kết"]
    },
    {
        "id": "attachment_styles",
        "domain": "Gắn bó",
        "type": "synthesis_application",
        "query": "Các kiểu gắn bó thời thơ ấu theo Bowlby và Ainsworth ảnh hưởng thế nào đến các mối quan hệ khi trưởng thành?",
        "expected_facets": ["an toàn", "lo âu", "né tránh", "Ainsworth", "Bowlby"]
    },
    {
        "id": "habit_loop",
        "domain": "Thói quen",
        "type": "concept_application",
        "query": "Vòng lặp thói quen gồm những yếu tố nào và làm thế nào để thay đổi một thói quen tiêu cực theo nghiên cứu tâm lý?",
        "expected_facets": ["gợi ý", "thói quen", "phần thưởng"]
    },
    {
        "id": "bias_confirmation",
        "domain": "Thiên kiến",
        "type": "concept_impact",
        "query": "Thiên kiến xác nhận (confirmation bias) là gì và nó dẫn đến những sai lầm nhận thức nào trong việc thu nhận thông tin?",
        "expected_facets": ["xác nhận", "tìm kiếm bằng chứng", "bỏ qua bằng chứng trái chiều"]
    },
    {
        "id": "stress_neurobiology",
        "domain": "Stress & Sang chấn",
        "type": "broad_synthesis",
        "query": "Sang chấn tâm lý và stress mãn tính ảnh hưởng như thế nào đến não bộ và cơ thể?",
        "expected_facets": ["hạch hạnh nhân", "cortisol", "cơ thể", "sang chấn"]
    },
    {
        "id": "research_causation",
        "domain": "Phương pháp nghiên cứu",
        "type": "methodology",
        "query": "Vì sao tương quan (correlation) không đồng nghĩa với quan hệ nhân quả (causation) trong nghiên cứu tâm lý học?",
        "expected_facets": ["tương quan", "nhân quả", "biến thứ ba", "thử nghiệm có kiểm soát"]
    },
    {
        "id": "insufficient_data",
        "domain": "Thiếu dữ liệu thư viện",
        "type": "unsupported_check",
        "query": "Theo các tài liệu trong thư viện, cơ chế tâm lý của hiện tượng du hành thời gian trong vật lý lượng tử là gì?",
        "expected_facets": ["chưa có dữ liệu", "không có căn cứ", "ngoài phạm vi thư viện"]
    },
    {
        "id": "narrow_regression",
        "domain": "Khái niệm cụ thể",
        "type": "narrow_concept",
        "query": "Khái niệm Cái bóng (Shadow) theo Carl Jung là gì?",
        "expected_facets": ["Cái bóng", "Carl Jung", "vô thức"]
    }
]


def load_partial_results(output_path: Path) -> Dict[str, Any]:
    if output_path.exists():
        try:
            return json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"results": []}


def save_partial_results(output_path: Path, data: Dict[str, Any]):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(output_path)


def run_benchmark(output_path: Path, tag: str = "evaluation_expanded"):
    agent = PsychologyAgent()
    data = load_partial_results(output_path)
    existing_results = {r["id"]: r for r in data.get("results", [])}

    print(f"=== Starting Incremental RAG Benchmark ({tag}): {len(BENCHMARK_QUERIES)} queries ===")
    print(f"    Already completed: {len(existing_results)} queries")

    for idx, item in enumerate(BENCHMARK_QUERIES, 1):
        qid = item["id"]
        query = item["query"]
        qtype = item["type"]
        domain = item["domain"]
        expected = item.get("expected_facets", [])

        if qid in existing_results:
            print(f"[{idx}/{len(BENCHMARK_QUERIES)}] Skipping already completed: {qid}")
            continue

        print(f"[{idx}/{len(BENCHMARK_QUERIES)}] Running {qid} ({domain})...", flush=True)

        start_time = time.time()
        # Acquire GPU lock for inference coordination
        with gpu_coordinator.acquire_for_inference():
            res = agent.process_query_sync(
                query=query,
                model=DEFAULT_CHAT_MODEL,
                embed_model=DEFAULT_EMBED_MODEL,
                temperature=0.2
            )
        elapsed = time.time() - start_time

        answer = res.get("answer", "")
        citations = res.get("citations", [])
        retrieval_trace = res.get("retrieval_trace", [])
        retrieved_books = res.get("retrieved_books", [])

        # Substantive facet coverage evaluation
        answer_lower = answer.lower()
        covered_facets = [f for f in expected if f.lower() in answer_lower]
        facet_coverage = round(len(covered_facets) / max(1, len(expected)), 2)

        record = {
            "id": qid,
            "domain": domain,
            "type": qtype,
            "query": query,
            "elapsed_seconds": round(elapsed, 2),
            "is_broad": res.get("is_broad", False),
            "is_truncated": res.get("is_truncated", False),
            "retrieved_chunk_count": len(retrieval_trace),
            "retrieved_books": retrieved_books,
            "citation_count": len(citations),
            "cited_books": list(dict.fromkeys(c.get("book_title", "") for c in citations if c.get("book_title"))),
            "expected_facets": expected,
            "covered_facets": covered_facets,
            "facet_coverage": facet_coverage,
            "answer_char_count": len(answer),
            "is_crisis": res.get("is_crisis", False),
            "answer": answer,
        }

        existing_results[qid] = record

        # Save incrementally after each query
        all_records = [existing_results[q["id"]] for q in BENCHMARK_QUERIES if q["id"] in existing_results]
        summary = {
            "tag": tag,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "completed_queries": len(all_records),
            "total_queries": len(BENCHMARK_QUERIES),
            "avg_char_count": round(sum(r["answer_char_count"] for r in all_records) / len(all_records), 1),
            "avg_citations": round(sum(r["citation_count"] for r in all_records) / len(all_records), 2),
            "avg_facet_coverage": round(sum(r.get("facet_coverage", 0) for r in all_records) / len(all_records), 2),
            "avg_elapsed_seconds": round(sum(r["elapsed_seconds"] for r in all_records) / len(all_records), 2),
            "results": all_records
        }
        save_partial_results(output_path, summary)

        print(
            f"    Done in {elapsed:.1f}s | Chars: {len(answer)} | Retrieved: {len(retrieval_trace)} | "
            f"Citations: {len(citations)} | Facet Cov: {facet_coverage*100:.0f}%",
            flush=True
        )

    print(f"=== Benchmark finished. Results saved to {output_path} ===")
    return summary


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "data" / "evaluation" / "rag-comparison-expanded-2026-10-01.json"
    tag = sys.argv[2] if len(sys.argv) > 2 else "expanded_rag"
    run_benchmark(out, tag)
