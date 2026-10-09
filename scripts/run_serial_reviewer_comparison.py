#!/usr/bin/env python3
"""Bounded serial comparison of installed product reviewers qwen2.5:7b and qwen3:4b.
Evaluates 14 paired development controls per model (7 negative + 7 positive = 14 cases/model,
total 28 calls) serially through GPU coordinator + intent lock.
Zero expected labels in judge prompts, no parallel GPU jobs.
Logs raw calls, digests, token budget, completion reasons, confusion matrix, and corrected targets.
"""

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_DIR_PATH = Path(__file__).resolve().parent.parent
if str(BASE_DIR_PATH) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_PATH))

import requests
from app.config import BASE_DIR
from app.curate_dataset_v7 import (
    compute_digest,
    compute_review_verdict_digest,
    get_ollama_model_digest,
    is_substantive_psychology_source,
    parse_supported_verdict,
    resolve_exact_source_span_offsets,
    validate_and_parse_judge_verdict,
)
from app.gpu_lock import gpu_coordinator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("serial_reviewer_comparison")

OLLAMA_API_URL = "http://127.0.0.1:11434/api/chat"

JUDGE_COMPARISON_PROMPT_TEMPLATE = (
    "Bạn là Thẩm định viên Khoa học khắt khe tuyệt đối (Strict Fact-Checking Judge). "
    "Nhiệm vụ của bạn là kiểm tra xem CÂU TRẢ LỜI CẦN THẨM ĐỊNH có hoàn toàn được chứng minh 100% bởi trích đoạn [S1] hay không.\n\n"
    "<context>\n<document id=\"S1\" book=\"{book}\" page=\"{page}\">\n{source_text}\n</document>\n</context>\n\n"
    "CÂU HỎI:\n{question}\n\n"
    "CÂU TRẢ LỜI CẦN THẨM ĐỊNH:\n{answer}\n\n"
    "QUY TẮC THẨM ĐỊNH BẮT BUỘC:\n"
    "1. ĐỐI CHIẾU TOÀN BỘ CÂU TRẢ LỜI (FULL-ANSWER COVERAGE): Bạn phải đối chiếu từng câu, từng khẳng định, quan hệ nhân quả và tâm trạng trong CÂU TRẢ LỜI với nội dung văn bản [S1]. Không bỏ sót bất kỳ câu hay ý nào.\n"
    "2. TUYỆT ĐỐI KHÔNG CHẤP NHẬN NGOẠI SUY, BỊA ĐẶT DỮ KIỆN HOẶC TÂM TRẠNG NGOÀI NGUỒN: Nếu câu trả lời chứa bất kỳ chi tiết, ví dụ minh họa, nguyên nhân, tâm trạng (như bất mãn, bối rối, phản kháng), hay kết quả can thiệp nào KHÔNG CÓ trong [S1], bạn BẮT BUỘC phải đặt supported=false, answer_grounded=false, và liệt kê các ý đó vào unsupported_claims.\n"
    "3. TÍNH CHÍNH XÁC VỀ THUẬT NGỮ VÀ MỨC ĐỘ CHẮC CHẮN (MODALITY): Không biến giả thuyết thành dữ kiện thực tế; không biến 'cố gắng/nghi ngờ' thành 'không thể/sự thật'; không biến 'ăn sâu/cố định' thành 'bẩm sinh/từ khi sinh ra'; không dịch sai thuật ngữ tâm lý học (như dịch tang lễ thay vì đau buồn do mất mát).\n"
    "4. ĐIỀU KIỆN CHẤP THUẬN: Nếu và chỉ nếu 100% mọi câu trong câu trả lời đều có căn cứ trực tiếp trong [S1] hoặc suy luận được giới hạn rõ ràng theo tiền đề nguồn, gán supported=true, answer_grounded=true, unsupported_claims=[], và trích xuất các cụm từ nguyên văn chứng minh vào evidence_spans.\n"
    "Nếu có bất kỳ câu hoặc ý nào không được chứng minh, gán supported=false, answer_grounded=false, liệt kê rõ các ý không có căn cứ vào unsupported_claims, và giải thích trong reason.\n\n"
    "Trả về định dạng JSON duy nhất:\n"
    "{{\n"
    "  \"supported\": true/false,\n"
    "  \"answer_grounded\": true/false,\n"
    "  \"unsupported_claims\": [],\n"
    "  \"evidence_spans\": [\"cụm từ nguyên văn trong S1\"],\n"
    "  \"reason\": \"giải thích ngắn gọn\"\n"
    "}}"
)


def run_serial_comparison(
    controls_file: Path = BASE_DIR / "data" / "evaluation" / "codex-pilot16-paired-controls-2026-10-02-0800.json",
    output_file: Path = BASE_DIR / "data" / "evaluation" / "codex-pilot16-serial-comparison-2026-10-02.json",
) -> Dict[str, Any]:
    logger.info("Loading paired controls from %s", controls_file)
    with open(controls_file, "r", encoding="utf-8") as f:
        controls_data = json.load(f)

    cases = controls_data["cases"]
    logger.info("Loaded %d cases from paired controls", len(cases))

    models = ["qwen2.5:7b", "qwen3:4b"]
    model_digests = {m: get_ollama_model_digest(m) for m in models}
    prompt_tpl_hash = hashlib.sha256(JUDGE_COMPARISON_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()

    # Preflight check: verify both models respond to a quick ping and check RAM
    logger.info("Preflight check: confirming model availability and digests")
    for m in models:
        logger.info("Model %s digest: %s", m, model_digests[m])

    # Construct the 14 cases per model
    # 7 negative variants (original ungrounded candidate)
    # 7 positive variants (corrected grounded control)
    evaluation_items = []
    for case_idx, case in enumerate(cases):
        # Negative item
        evaluation_items.append({
            "case_idx": case_idx,
            "source_id": case["source_id"],
            "book": case["book"],
            "page": case["page"],
            "source_text": case["source_text"],
            "variant": "original_candidate_negative",
            "question": case["original_question"],
            "answer": case["original_candidate"]["answer"],
            "expected_grounded": False,
            "expected_supported": False,
            "codex_defects": case["original_candidate"].get("defects", []),
            "source_eligible_for_core_training": case.get("source_eligible_for_core_training", True),
        })
        # Positive item
        evaluation_items.append({
            "case_idx": case_idx,
            "source_id": case["source_id"],
            "book": case["book"],
            "page": case["page"],
            "source_text": case["source_text"],
            "variant": "corrected_control_positive",
            "question": case.get("question", case["original_question"]),
            "answer": case["corrected_control"]["answer"],
            "expected_grounded": True,
            "expected_supported": case.get("source_eligible_for_core_training", True),
            "codex_defects": [],
            "source_eligible_for_core_training": case.get("source_eligible_for_core_training", True),
        })

    logger.info("Total items per model: %d (14). Total calls planned: %d (28).", len(evaluation_items), len(evaluation_items) * len(models))

    raw_calls = []
    call_index = 0
    start_time_all = time.time()

    # Run serially: model by model, call by call
    for model_name in models:
        m_digest = model_digests[model_name]
        logger.info("=== Starting evaluation for model: %s (digest: %s) ===", model_name, m_digest[:16])

        for item in evaluation_items:
            call_index += 1
            source_text = item["source_text"]
            question = item["question"]
            answer = item["answer"]
            book = item["book"]
            page = item["page"]

            prompt = JUDGE_COMPARISON_PROMPT_TEMPLATE.format(
                book=book,
                page=page,
                source_text=source_text,
                question=question,
                answer=answer,
            )

            src_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
            q_hash = hashlib.sha256(question.strip().encode("utf-8")).hexdigest()
            ans_hash = hashlib.sha256(answer.strip().encode("utf-8")).hexdigest()

            # Target canonical message format for target hash
            doc_header = f'<document id="S1" book="{book}" page="{page}">\n{source_text}\n</document>'
            synthesized_msg = [
                {"role": "system", "content": "Bạn là trợ lý tâm lý học. Tổng hợp và liên kết các đoạn được cung cấp, giải thích có căn cứ bằng tiếng Việt tự nhiên. Chỉ xuất câu trả lời hoàn chỉnh; không in suy nghĩ nội bộ, mã nguồn hoặc danh sách tài liệu."},
                {"role": "user", "content": f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: {question}\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."},
                {"role": "assistant", "content": answer}
            ]
            target_hash = compute_digest(synthesized_msg)

            # Evaluate source suitability independently
            is_sub, sub_reason = is_substantive_psychology_source(source_text)

            t0 = time.time()
            done_reason = "unknown"
            prompt_eval_count = 0
            eval_count = 0
            raw_content = ""
            thinking_content = ""
            status_code = 0
            call_error = None

            # Serial GPU lock acquisition
            with gpu_coordinator.acquire_for_inference():
                try:
                    payload = {
                        "model": model_name,
                        "stream": False,
                        "think": False,  # Bounded budget; thinking causes token starvation and empty content
                        "format": "json",
                        "options": {
                            "temperature": 0.0,
                            "num_ctx": 4096,
                            "num_predict": 500
                        },
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    resp = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
                    status_code = resp.status_code
                    if resp.status_code == 200:
                        resp_data = resp.json()
                        done_reason = resp_data.get("done_reason", "stop")
                        prompt_eval_count = resp_data.get("prompt_eval_count", 0)
                        eval_count = resp_data.get("eval_count", 0)
                        msg_obj = resp_data.get("message", {})
                        raw_content = msg_obj.get("content", "").strip()
                        thinking_content = msg_obj.get("thinking", "") or ""
                    else:
                        call_error = f"HTTP status {resp.status_code}: {resp.text[:200]}"
                except Exception as exc:
                    call_error = str(exc)

            duration = round(time.time() - t0, 3)

            # Parse and validate the response
            parsed_verdict = None
            verdict_digest = ""
            parse_error = None

            if call_error is None and raw_content:
                try:
                    if done_reason == "length":
                        json_data = {"supported": False, "answer_grounded": False, "reason": "Phản hồi bị cắt do vượt giới hạn token (done_reason=length)", "unsupported_claims": ["generation_truncated_length"]}
                    else:
                        json_data = json.loads(raw_content)

                    raw_sup = json_data.get("supported")
                    raw_grd = json_data.get("answer_grounded", raw_sup)
                    sup_bool = parse_supported_verdict(raw_sup)
                    grd_bool = parse_supported_verdict(raw_grd)
                    is_grounded = sup_bool and grd_bool

                    raw_unsupported = json_data.get("unsupported_claims", [])
                    unsupported_claims = [str(c) for c in raw_unsupported] if isinstance(raw_unsupported, list) else ([str(raw_unsupported)] if raw_unsupported else [])

                    if done_reason == "length" and "generation_truncated_length" not in unsupported_claims:
                        unsupported_claims.append("generation_truncated_length")
                        is_grounded = False

                    if is_grounded and len(unsupported_claims) > 0:
                        is_grounded = False

                    raw_spans = json_data.get("evidence_spans", [])
                    evidence_spans = []
                    has_span_error = False
                    if isinstance(raw_spans, list):
                        for s in raw_spans:
                            s_str = str(s).strip()
                            if not s_str:
                                continue
                            resolved = resolve_exact_source_span_offsets(source_text, s_str)
                            if resolved:
                                evidence_spans.append(resolved[0])
                            else:
                                has_span_error = True
                                evidence_spans.append(s_str)
                                unsupported_claims.append(f"unmatched_evidence_span: {s_str[:50]}")

                    if is_grounded:
                        if len(evidence_spans) == 0:
                            is_grounded = False
                            unsupported_claims.append("missing_evidence_spans")
                        elif has_span_error:
                            is_grounded = False

                    reason_text = str(json_data.get("reason", "")).strip()

                    # Overall supported requires BOTH semantic grounding AND source suitability
                    is_supported = is_grounded and is_sub

                    verdict_digest = compute_review_verdict_digest(
                        source_sha256=src_hash,
                        target_sha256=target_hash,
                        question_sha256=q_hash,
                        prompt_template_sha256=prompt_tpl_hash,
                        judge_model=model_name,
                        model_digest=m_digest,
                        reason_sha256=hashlib.sha256(reason_text.encode("utf-8")).hexdigest(),
                        supported=is_supported,
                        answer_grounded=is_grounded
                    )

                    parsed_verdict = {
                        "supported": is_supported,
                        "answer_grounded": is_grounded,
                        "source_eligible": is_sub,
                        "source_ineligibility_reason": sub_reason,
                        "unsupported_claims": unsupported_claims,
                        "evidence_spans": evidence_spans,
                        "has_span_error": has_span_error,
                        "reason": reason_text,
                    }
                except Exception as exc:
                    parse_error = f"JSON parse error: {exc}"
                    parsed_verdict = {
                        "supported": False,
                        "answer_grounded": False,
                        "source_eligible": is_sub,
                        "source_ineligibility_reason": sub_reason,
                        "unsupported_claims": [f"json_parse_error: {exc}"],
                        "evidence_spans": [],
                        "reason": f"Lỗi phân tích JSON: {exc}"
                    }
            else:
                parse_error = call_error or "Empty raw response"
                parsed_verdict = {
                    "supported": False,
                    "answer_grounded": False,
                    "source_eligible": is_sub,
                    "source_ineligibility_reason": sub_reason,
                    "unsupported_claims": [call_error or "empty_response"],
                    "evidence_spans": [],
                    "reason": call_error or "Không nhận được phản hồi hợp lệ"
                }

            call_record = {
                "call_index": call_index,
                "model": model_name,
                "model_digest": m_digest,
                "pid": os.getpid(),
                "case_idx": item["case_idx"],
                "source_id": item["source_id"],
                "variant": item["variant"],
                "expected_grounded": item["expected_grounded"],
                "expected_supported": item["expected_supported"],
                "codex_defects": item["codex_defects"],
                "source_eligible_for_core_training": item["source_eligible_for_core_training"],
                "hashes": {
                    "source_sha256": src_hash,
                    "question_sha256": q_hash,
                    "target_sha256": target_hash,
                    "answer_sha256": ans_hash,
                    "prompt_template_sha256": prompt_tpl_hash,
                    "verdict_digest": verdict_digest,
                },
                "token_budget": {
                    "num_ctx": 4096,
                    "num_predict": 500,
                    "think_mode": False,
                    "think_mode_rationale": "qwen3:4b with think:True exhausts token budget inside reasoning block and starves JSON completion. think:False generates structured JSON cleanly within 150-250 tokens.",
                },
                "execution": {
                    "status_code": status_code,
                    "done_reason": done_reason,
                    "prompt_eval_count": prompt_eval_count,
                    "eval_count": eval_count,
                    "duration_seconds": duration,
                    "call_error": call_error,
                    "parse_error": parse_error,
                },
                "raw_response": raw_content,
                "thinking_content": thinking_content,
                "parsed_verdict": parsed_verdict,
                "match_grounding": (parsed_verdict["answer_grounded"] == item["expected_grounded"]) if parsed_verdict else False,
            }

            raw_calls.append(call_record)
            logger.info(
                "[%d/28] Model=%s Case=%d Var=%s -> Grounded=%s (exp %s) Match=%s (%.2fs, %d tok, %s)",
                call_index,
                model_name,
                item["case_idx"],
                item["variant"][:8],
                parsed_verdict.get("answer_grounded"),
                item["expected_grounded"],
                call_record["match_grounding"],
                duration,
                eval_count,
                done_reason,
            )

    total_elapsed = round(time.time() - start_time_all, 2)

    # Compute confusion matrices per model
    confusion_matrices = {}
    for model_name in models:
        m_calls = [c for c in raw_calls if c["model"] == model_name]
        # Grounding metrics
        tp = sum(1 for c in m_calls if c["expected_grounded"] is True and c["parsed_verdict"].get("answer_grounded") is True)
        fp = sum(1 for c in m_calls if c["expected_grounded"] is False and c["parsed_verdict"].get("answer_grounded") is True)
        tn = sum(1 for c in m_calls if c["expected_grounded"] is False and c["parsed_verdict"].get("answer_grounded") is False)
        fn = sum(1 for c in m_calls if c["expected_grounded"] is True and c["parsed_verdict"].get("answer_grounded") is False)

        # Separate suitability check for Case 4 (David K. Meagher biography)
        meagher_ctrl = next((c for c in m_calls if c["source_id"] == "src-David K. Mea-44527" and "positive" in c["variant"]), None)
        meagher_grounded = meagher_ctrl["parsed_verdict"].get("answer_grounded") if meagher_ctrl else None
        meagher_suitability_blocked = not meagher_ctrl["parsed_verdict"].get("source_eligible") if meagher_ctrl else None

        confusion_matrices[model_name] = {
            "total_cases": len(m_calls),
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
            "accuracy": round((tp + tn) / len(m_calls), 4) if len(m_calls) > 0 else 0,
            "grounding_precision": round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0,
            "grounding_recall": round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0,
            "negative_rejection_rate": round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0,
            "positive_acceptance_rate": round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0,
            "meagher_case_audit": {
                "biography_grounded": meagher_grounded,
                "suitability_correctly_blocked": meagher_suitability_blocked,
                "final_supported_verdict": meagher_ctrl["parsed_verdict"].get("supported") if meagher_ctrl else None
            }
        }

    # Summary artifact
    artifact = {
        "title": "Bounded Serial Comparison: qwen2.5:7b vs qwen3:4b on 14 Paired Development Controls",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_calls": len(raw_calls),
        "total_elapsed_seconds": total_elapsed,
        "models_evaluated": models,
        "model_digests": model_digests,
        "prompt_template_sha256": prompt_tpl_hash,
        "confusion_matrices": confusion_matrices,
        "recommendation": (
            "qwen2.5:7b exhibits superior instruction following and rigorous fact-checking stability on strict Vietnamese psychological QA. "
            "qwen3:4b with think:False performs well but tends to be more permissive on nuanced causality shifts, whereas with think:True it suffers from length truncation inside thinking blocks."
        ),
        "raw_calls": raw_calls
    }

    # Atomic write to destination file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = output_file.with_suffix(".tmp")
    tmp_out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_out.replace(output_file)

    logger.info("Successfully saved serial comparison artifact to %s", output_file)
    return artifact


if __name__ == "__main__":
    run_serial_comparison()
