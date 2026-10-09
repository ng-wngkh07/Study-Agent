"""Isolated unit and integration test suite for curation-release gates,
worker control, judge parsing, and provenance verification.
All tests run in temporary directories without mutating project data or starting MLX.
"""

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
import pytest

from app.curate_dataset_v7 import (
    parse_supported_verdict,
    is_truncated_source_text,
    compute_digest,
    compute_curation_cache_key,
    compute_curation_plan_hash,
    publish_v7_dataset,
    ensure_judge_calibrated,
    curate_candidates_workspace,
    WorkerLock,
    FROZEN_HOLDOUT_BOOKS,
    compute_review_verdict_digest,
    get_synthetic_registry,
    get_ollama_model_digest,
    JUDGE_PROMPT_TEMPLATE,
    assign_group_partition,
    CALIBRATION_PROTOCOL_VERSION,
    is_valid_cached_judge_verdict,
    is_substantive_psychology_source,
    resolve_exact_source_span_offsets,
    truncate_to_sentence_boundary,
    segment_text_into_sentences,
    validate_vietnamese_semantic_text,
    validate_claim_map,
    validate_and_parse_judge_verdict
)
from app.config import BASE_DIR, DB_PATH
from app.text_cleaner import sanitize_for_prompt_context


def test_parse_supported_verdict():
    """Verify strict parsing: string 'false' and 'False' must NOT evaluate to True."""
    assert parse_supported_verdict(True) is True
    assert parse_supported_verdict(False) is False
    assert parse_supported_verdict("true") is True
    assert parse_supported_verdict("True") is True
    assert parse_supported_verdict("false") is False
    assert parse_supported_verdict("False") is False
    assert parse_supported_verdict("0") is False
    assert parse_supported_verdict("no") is False
    assert parse_supported_verdict(None) is False
    assert parse_supported_verdict({}) is False


def test_truncated_source_text_detection():
    """Verify detection of dangling OCR fragments and incomplete sentences."""
    # Complete sentence
    assert is_truncated_source_text("Đây là một câu trọn vẹn và hoàn chỉnh.") is False
    assert is_truncated_source_text("Lý thuyết hành vi được Skinner phát triển.") is False

    # Dangling word from Sức mạnh của thói quen p119
    assert is_truncated_source_text("Lề thói được lập trình sẵn – Hãy tò mò, Nói điều không ai nói, Áp d") is True
    # Dangling hyphen
    assert is_truncated_source_text("Nhân viên được huấn luyện phương pháp -") is True
    # Trailing comma
    assert is_truncated_source_text("Khi gợi ý đến, hành động xảy ra,") is True


def test_cache_key_binds_all_parameters():
    """Changing source, facet, model, or prompt template MUST change cache key."""
    k1 = compute_curation_cache_key("text_a", "overview", "teacher_7b", "judge_7b", "pt1", "pj1", teacher_model_digest="dt1", judge_model_digest="dj1")
    k2 = compute_curation_cache_key("text_a", "overview", "teacher_7b", "judge_7b", "pt1", "pj1", teacher_model_digest="dt1", judge_model_digest="dj1")
    assert k1 == k2

    # Different text
    assert k1 != compute_curation_cache_key("text_b", "overview", "teacher_7b", "judge_7b", "pt1", "pj1", teacher_model_digest="dt1", judge_model_digest="dj1")
    # Different facet
    assert k1 != compute_curation_cache_key("text_a", "deep_dive", "teacher_7b", "judge_7b", "pt1", "pj1", teacher_model_digest="dt1", judge_model_digest="dj1")
    # Different teacher model
    assert k1 != compute_curation_cache_key("text_a", "overview", "teacher_3b", "judge_7b", "pt1", "pj1", teacher_model_digest="dt1", judge_model_digest="dj1")
    # Different judge model
    assert k1 != compute_curation_cache_key("text_a", "overview", "teacher_7b", "judge_4b", "pt1", "pj1", teacher_model_digest="dt1", judge_model_digest="dj1")
    # Different prompt template
    assert k1 != compute_curation_cache_key("text_a", "overview", "teacher_7b", "judge_7b", "pt2", "pj1", teacher_model_digest="dt1", judge_model_digest="dj1")


def test_worker_lock_serialization(tmp_path):
    """Verify single-owner lock on curation worker."""
    lock_file = tmp_path / "test_worker.lock"
    lock1 = WorkerLock(lock_path=lock_file)
    lock2 = WorkerLock(lock_path=lock_file)

    assert lock1.acquire() is True
    assert lock2.acquire() is False

    lock1.release()
    assert lock2.acquire() is True
    lock2.release()


def test_publish_overwrite_protection(tmp_path):
    """Publishing must fail-closed if destination already contains approved release."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_published"
    publish_dir.mkdir()

    # Pre-populate publish_dir with release artifact
    (publish_dir / "approved_manifest.jsonl").write_text("manifest content")

    (work_dir / "accepted.jsonl").write_text(json.dumps({
        "type": "synthetic_curriculum",
        "partition": "train",
        "messages": [{"role": "user", "content": "q"}],
        "review_evidence": {"supported": True}
    }) + "\n")

    with pytest.raises(FileExistsError, match="CHẶN XUẤT BẢN"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_unbound_source_rejected(tmp_path):
    """Gate must reject candidate whose source does not exist in the database."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7"

    fake_cand = {
        "source_id": "src-nonexistent-999999999",
        "chunk_id": 999999999,
        "book": "Sách không có thật",
        "page": 1,
        "partition": "train",
        "messages": [
            {"role": "user", "content": "Hỏi"},
            {"role": "assistant", "content": "Đáp"}
        ],
        "review_evidence": {
            "supported": True,
            "answer_grounded": True,
            "verdict_digest": "v_fake",
            "source_sha256": "s_fake",
            "target_sha256": "t_fake"
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(fake_cand) + "\n")

    with pytest.raises(ValueError, match="CHẶN XUẤT BẢN: Cổng nghiệm thu chất lượng dữ liệu chưa đạt"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_injected_holdout_source_rejected(tmp_path):
    """Gate must reject candidate that uses a holdout chunk even with a forged book title."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7"

    # Find a real chunk from a holdout book in DB
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, d.file_hash FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename LIKE '%1241-thien-tai%' OR c.filename LIKE '%dac_nhan_tam%' LIMIT 1"
        ).fetchone()

    assert row is not None, "Could not find holdout chunk in DB"
    chunk_id = row["id"]
    safe_text = sanitize_for_prompt_context(row["text"][:750])
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()

    msg = [
        {"role": "user", "content": "Hỏi"},
        {"role": "assistant", "content": "Đáp câu trả lời duy nhất"}
    ]
    target_hash = compute_digest(msg)

    # Candidate with FORGED display title "Sách Tâm Lý An Toàn"
    cand = {
        "source_id": f"src-safe-{chunk_id}",
        "chunk_id": chunk_id,
        "book": "Sách Tâm Lý An Toàn",  # Forged title!
        "page": 10,
        "partition": "train",
        "messages": msg,
        "review_evidence": {
            "supported": True,
            "answer_grounded": True,
            "verdict_digest": "digest123",
            "source_sha256": src_hash,
            "target_sha256": target_hash
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="RÒ RỈ HOLDOUT"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_tampered_target_rejected(tmp_path):
    """Gate must reject candidate whose assistant message was tampered after review."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    safe_text = sanitize_for_prompt_context(row["text"][:750])
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()

    orig_msg = [
        {"role": "user", "content": "Hỏi gốc"},
        {"role": "assistant", "content": "Đáp gốc"}
    ]
    target_hash_at_review = compute_digest(orig_msg)

    # TAMPERED message content
    tampered_msg = [
        {"role": "user", "content": "Hỏi gốc"},
        {"role": "assistant", "content": "Đáp ĐÃ BỊ SỬA ĐỔI SAU THẨM ĐỊNH"}
    ]

    cand = {
        "source_id": f"src-valid-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": 10,
        "partition": "train",
        "messages": tampered_msg,  # Tampered!
        "review_evidence": {
            "supported": True,
            "answer_grounded": True,
            "verdict_digest": "v_hash",
            "source_sha256": src_hash,
            "target_sha256": target_hash_at_review  # Mismatched!
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="tampered target"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_duplicate_assistant_answer_rejected(tmp_path):
    """Gate must reject duplicate assistant answers paired with different user prompts."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT c.id, c.text, c.filename FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' LIMIT 2"
        ).fetchall()

    row1, row2 = rows[0], rows[1]
    same_answer = "Câu trả lời y hệt nhau dùng chung cho hai ngữ cảnh khác nhau."

    cand1 = {
        "source_id": f"src-a-{row1['id']}",
        "chunk_id": row1["id"],
        "book": row1["filename"],
        "page": 1,
        "partition": "train",
        "messages": [
            {"role": "user", "content": "Câu hỏi số 1"},
            {"role": "assistant", "content": same_answer}
        ],
        "review_evidence": {
            "supported": True,
            "answer_grounded": True,
            "verdict_digest": "v1",
            "source_sha256": hashlib.sha256(sanitize_for_prompt_context(row1["text"][:750]).encode()).hexdigest(),
            "target_sha256": compute_digest([{"role": "user", "content": "Câu hỏi số 1"}, {"role": "assistant", "content": same_answer}])
        }
    }

    cand2 = {
        "source_id": f"src-b-{row2['id']}",
        "chunk_id": row2["id"],
        "book": row2["filename"],
        "page": 2,
        "partition": "train",
        "messages": [
            {"role": "user", "content": "Câu hỏi số 2 hoàn toàn khác"},
            {"role": "assistant", "content": same_answer}  # Duplicate!
        ],
        "review_evidence": {
            "supported": True,
            "answer_grounded": True,
            "verdict_digest": "v2",
            "source_sha256": hashlib.sha256(sanitize_for_prompt_context(row2["text"][:750]).encode()).hexdigest(),
            "target_sha256": compute_digest([{"role": "user", "content": "Câu hỏi số 2 hoàn toàn khác"}, {"role": "assistant", "content": same_answer}])
        }
    }

    (work_dir / "accepted.jsonl").write_text(json.dumps(cand1) + "\n" + json.dumps(cand2) + "\n")

    with pytest.raises(ValueError, match="duplicate assistant answer"):
        publish_v7_dataset(work_dir, publish_dir, min_train=2, min_valid=0, min_groups=1)


def test_judge_calibration_fail_closed(monkeypatch):
    """Judge calibration gate must fail-closed (raise RuntimeError) when any control case fails."""
    import app.curate_dataset_v7 as cur_mod

    def mock_failing_calibration(judge_model="qwen2.5:7b"):
        return {
            "judge_model": judge_model,
            "all_passed": False,
            "cases": [{"id": "calib_numeric_error", "match": False, "reason": "lenient_error"}]
        }

    monkeypatch.setattr(cur_mod, "run_judge_calibration", mock_failing_calibration)
    with pytest.raises(RuntimeError, match="CHẶN QUY TRÌNH.*không vượt qua kiểm định chuẩn hóa"):
        cur_mod.ensure_judge_calibrated(judge_model="qwen2.5:7b")


def test_worker_lock_context_manager(tmp_path):
    """WorkerLock context manager must acquire lock, block concurrent, and release on exit or exception."""
    lock_file = tmp_path / "cm_worker.lock"

    with WorkerLock(lock_path=lock_file) as lock1:
        # Concurrent acquisition within block must fail
        lock2 = WorkerLock(lock_path=lock_file)
        assert lock2.acquire() is False

    # After exiting block, lock must be free
    lock3 = WorkerLock(lock_path=lock_file)
    assert lock3.acquire() is True
    lock3.release()

    # Exception inside block must still release lock
    try:
        with WorkerLock(lock_path=lock_file):
            raise ValueError("Test error inside lock block")
    except ValueError:
        pass

    lock4 = WorkerLock(lock_path=lock_file)
    assert lock4.acquire() is True
    lock4.release()


def test_checkpoint_plan_hash_mismatch_rejected(tmp_path, monkeypatch):
    """Resume must fail-closed if checkpoint plan_hash does not match current plan hash."""
    import app.curate_dataset_v7 as cur_mod

    # Mock calibration to pass without GPU call
    monkeypatch.setattr(cur_mod, "ensure_judge_calibrated", lambda judge_model: {"all_passed": True})

    work_dir = tmp_path / "work_chk_mismatch"
    work_dir.mkdir()
    chk_file = work_dir / "checkpoint.json"

    # Write checkpoint with mismatched plan_hash
    chk_file.write_text(json.dumps({
        "status": "paused",
        "stage": "data_preparation_candidates",
        "plan_hash": "stale_hash_from_old_prompt_revision_12345",
        "processed_sources": 50,
        "total_sources": 100
    }))

    with pytest.raises(RuntimeError, match="CHẶN TIẾP TỤC.*Checkpoint plan_hash không khớp"):
        curate_candidates_workspace(work_dir, max_sources_to_curate=5)


def test_checkpoint_corrupted_json_rejected(tmp_path, monkeypatch):
    """Worker must raise RuntimeError if checkpoint.json contains corrupted/malformed JSON."""
    import app.curate_dataset_v7 as cur_mod

    monkeypatch.setattr(cur_mod, "ensure_judge_calibrated", lambda judge_model: {"all_passed": True})

    work_dir = tmp_path / "work_corrupted_chk"
    work_dir.mkdir()
    chk_file = work_dir / "checkpoint.json"
    chk_file.write_text("{ incomplete_json: ")

    with pytest.raises(RuntimeError, match="CHẶN TIẾP TỤC.*Tệp checkpoint bị hỏng"):
        curate_candidates_workspace(work_dir, max_sources_to_curate=5)


def test_accepted_jsonl_corrupted_line_rejected(tmp_path, monkeypatch):
    """Worker must raise RuntimeError if accepted.jsonl contains malformed JSON."""
    import app.curate_dataset_v7 as cur_mod

    monkeypatch.setattr(cur_mod, "ensure_judge_calibrated", lambda judge_model: {"all_passed": True})

    work_dir = tmp_path / "work_corrupted_acc"
    work_dir.mkdir()
    acc_file = work_dir / "accepted.jsonl"
    acc_file.write_text('{"type": "synthetic"}\nNOT_VALID_JSON\n')

    with pytest.raises(RuntimeError, match="CHẶN KHỞI ĐỘNG.*Tệp accepted.jsonl bị lỗi cú pháp"):
        curate_candidates_workspace(work_dir, max_sources_to_curate=5)


def test_rejection_record_schema_completeness():
    """Verify that rejected records in candidate pool contain all required audit fields."""
    rejected_file = BASE_DIR / "data" / "training" / "v7_candidates" / "rejected.jsonl"
    if not rejected_file.exists():
        pytest.skip("rejected.jsonl does not exist yet")

    records = [json.loads(line) for line in rejected_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) > 0, "No records in rejected.jsonl"

    for r in records[-5:]:  # Check newly added rejections
        assert "source_id" in r
        assert "reason" in r
        assert "judge_model" in r
        assert "timestamp" in r


def test_known_defects_isolated_from_candidate_pool():
    """Verify that known defective candidates (19733, 36308) are completely absent from accepted and present in rejected."""
    candidates_dir = BASE_DIR / "data" / "training" / "v7_candidates"
    accepted_file = candidates_dir / "accepted.jsonl"
    rejected_file = candidates_dir / "rejected.jsonl"

    if not accepted_file.exists() or not rejected_file.exists():
        pytest.skip("Candidate pool files do not exist")

    acc_text = accepted_file.read_text(encoding="utf-8")
    rej_text = rejected_file.read_text(encoding="utf-8")

    assert "src-5446-suc-man-19733" not in acc_text, "Defect 19733 found in accepted.jsonl!"
    assert "src-473711314-Ta-36308" not in acc_text, "Defect 36308 found in accepted.jsonl!"
    for pilot_id in [
        "src-phi_ly_tri.p-33318",
        "src-5446-suc-man-19437",
        "src-5600-tu-duy--20068",
        "src-Carol Dweck -39672",
        "src-David K. Mea-44527",
        "src-Hal Blumenfe-25331",
        "src-Lori Gottlie-28283",
    ]:
        assert pilot_id not in acc_text, f"Pilot defect {pilot_id} found in accepted.jsonl!"

    assert "src-5446-suc-man-19733" in rej_text, "Defect 19733 not recorded in rejected.jsonl!"
    assert "src-473711314-Ta-36308" in rej_text, "Defect 36308 not recorded in rejected.jsonl!"
    for pilot_id in [
        "src-phi_ly_tri.p-33318",
        "src-5446-suc-man-19437",
        "src-5600-tu-duy--20068",
        "src-Carol Dweck -39672",
        "src-David K. Mea-44527",
        "src-Hal Blumenfe-25331",
        "src-Lori Gottlie-28283",
    ]:
        assert pilot_id in rej_text, f"Pilot defect {pilot_id} not recorded in rejected.jsonl!"


def test_probe_1_fabricated_review_rejected(tmp_path):
    """Probe 1: Gate must reject candidate with matching hashes but fabricated/unbound verdict_digest."""
    work_dir = tmp_path / "work_p1"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p1"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, c.book_title, c.page_num FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    safe_text = sanitize_for_prompt_context(row["text"][:750])
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
    doc_header = f'<document id="S1" book="{row["book_title"]}" page="{row["page_num"]}">\n{safe_text}\n</document>'
    msg = [
        {"role": "system", "content": "Bạn là trợ lý tâm lý học."},
        {"role": "user", "content": f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: Nội dung đoạn trích là gì?\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."},
        {"role": "assistant", "content": "Nội dung đoạn trích giải thích chi tiết các dữ kiện [S1]."}
    ]
    target_hash = compute_digest(msg)

    cand = {
        "source_id": f"src-p1-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": row["page_num"],
        "partition": "train",
        "messages": msg,
        "review_evidence": {
            "judge_model": "qwen2.5:7b",
            "model_digest": get_ollama_model_digest("qwen2.5:7b"),
            "supported": True,
            "answer_grounded": True,
            "reason": "Một lý do bất kỳ",
            "verdict_digest": "v_fake_fabricated_digest_12345",  # Fabricated!
            "source_sha256": src_hash,
            "target_sha256": target_hash,
            "prompt_template_sha256": hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest(),
            "full_verdict": {
                "supported": True,
                "answer_grounded": True,
                "judge_model": "qwen2.5:7b",
                "reason": "Một lý do bất kỳ",
                "unsupported_claims": []
            }
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="fabricated review proof"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_2_false_string_in_review_rejected(tmp_path):
    """Probe 2: Gate must reject string 'false' in supported / answer_grounded (strict boolean schema)."""
    work_dir = tmp_path / "work_p2"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p2"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, c.book_title, c.page_num FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    safe_text = sanitize_for_prompt_context(row["text"][:750])
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
    doc_header = f'<document id="S1" book="{row["book_title"]}" page="{row["page_num"]}">\n{safe_text}\n</document>'
    msg = [
        {"role": "system", "content": "Bạn là trợ lý tâm lý học."},
        {"role": "user", "content": f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: Nội dung?\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."},
        {"role": "assistant", "content": "Nội dung câu trả lời [S1]."}
    ]

    cand = {
        "source_id": f"src-p2-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": row["page_num"],
        "partition": "train",
        "messages": msg,
        "review_evidence": {
            "judge_model": "qwen2.5:7b",
            "supported": "false",  # String 'false'!
            "answer_grounded": "false",
            "verdict_digest": "digest",
            "source_sha256": src_hash,
            "target_sha256": compute_digest(msg)
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="không phải boolean True hợp lệ"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_3_synthetic_type_bypasses_source_rejected(tmp_path):
    """Probe 3: Gate must reject arbitrary/forged synthetic type that does not match canonical registry."""
    work_dir = tmp_path / "work_p3"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p3"

    forged_synthetic = {
        "type": "synthetic_curriculum",
        "kind": "forged_math",
        "facet": "fake_derivation",
        "partition": "train",
        "messages": [
            {"role": "user", "content": "Câu hỏi bịa không có trong registry"},
            {"role": "assistant", "content": "Câu trả lời bịa"}
        ],
        "review_evidence": {
            "supported": True,
            "answer_grounded": True,
            "verdict_digest": "v_syn_fake"
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(forged_synthetic) + "\n")

    with pytest.raises(ValueError, match="không tồn tại trong canonical registry"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_source_group_train_valid_overlap_rejected(tmp_path):
    """Gate must reject release if any book-chapter group overlaps between train and valid."""
    work_dir = tmp_path / "work_overlap"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_overlap"

    # Both samples share group "test_book.pdf:0"
    cand_train = {
        "type": "synthetic_curriculum",
        "book": "test_book.pdf",
        "page": 5,
        "partition": "train",
        "messages": [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}],
        "review_evidence": {"supported": True, "answer_grounded": True}
    }
    cand_valid = {
        "type": "synthetic_curriculum",
        "book": "test_book.pdf",
        "page": 10,  # Same group bucket 10 // 15 == 0!
        "partition": "valid",
        "messages": [{"role": "user", "content": "q2"}, {"role": "assistant", "content": "a2"}],
        "review_evidence": {"supported": True, "answer_grounded": True}
    }

    # Use real canonical items to pass synthetic check, but assign overlapping book/page
    registry = get_synthetic_registry()
    items = list(registry.values())[:2]
    cand_train = dict(items[0])
    cand_train["book"] = "test_book.pdf"
    cand_train["page"] = 5
    cand_train["partition"] = "train"
    cand_train["review_evidence"] = {"supported": True, "answer_grounded": True}

    cand_valid = dict(items[1])
    cand_valid["book"] = "test_book.pdf"
    cand_valid["page"] = 10
    cand_valid["partition"] = "valid"
    cand_valid["review_evidence"] = {"supported": True, "answer_grounded": True}

    (work_dir / "accepted.jsonl").write_text(json.dumps(cand_train) + "\n" + json.dumps(cand_valid) + "\n")

    with pytest.raises(ValueError, match="source-group overlap"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=1, min_groups=1)


def test_model_digest_changes_plan_hash_and_cache_key():
    """Changing model digest must change both curation plan hash and cache key."""
    # Cache key
    k1 = compute_curation_cache_key("text_a", "overview", "teacher_7b", "judge_7b", teacher_model_digest="d1", judge_model_digest="d1")
    k2 = compute_curation_cache_key("text_a", "overview", "teacher_7b", "judge_7b", teacher_model_digest="d2", judge_model_digest="d1")
    assert k1 != k2

    # Plan hash
    sources = [{"id": "s1", "chunk_id": 1, "filename": "b.pdf", "partition": "train", "text": "sample"}]
    p1 = compute_curation_plan_hash(sources, "teacher_7b", "judge_7b", teacher_model_digest="d1", judge_model_digest="d1")
    p2 = compute_curation_plan_hash(sources, "teacher_7b", "judge_7b", teacher_model_digest="d2", judge_model_digest="d1")
    assert p1 != p2


def test_positive_publish_path(tmp_path, monkeypatch):
    """Positive test path: Valid extracted candidate + valid synthetic item pass all release gates."""
    import app.curate_dataset_v7 as cur_mod

    # Mock context token audit to pass in temporary test directory
    monkeypatch.setattr(cur_mod, "audit_context_truncation", lambda staging_dir, max_seq_length: {"acceptable": True})

    work_dir = tmp_path / "work_pos"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_pos"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, c.book_title, c.page_num FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' AND LENGTH(c.text) >= 150 LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    safe_text = cur_mod.extract_complete_source_text(row["text"], max_chars=900)
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
    doc_header = f'<document id="S1" book="{row["book_title"]}" page="{row["page_num"]}">\n{safe_text}\n</document>'
    user_content = f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: Phân tích nội dung đoạn trích [S1]?\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."
    assistant_content = "Đoạn trích [S1] trình bày các luận điểm then chốt một cách xác thực."
    msg = [
        {"role": "system", "content": cur_mod.SYSTEM_PROMPT_TRAIN},
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": assistant_content}
    ]
    target_hash = compute_digest(msg)
    q_hash = hashlib.sha256("Phân tích nội dung đoạn trích [S1]?".encode("utf-8")).hexdigest()
    prompt_tpl_hash = hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
    reason_str = "Đoạn trích cung cấp đầy đủ căn cứ xác thực cho câu trả lời đề xuất."
    judge_model = "qwen2.5:7b"
    m_digest = get_ollama_model_digest(judge_model)

    verdict_hash = compute_review_verdict_digest(
        source_sha256=src_hash,
        target_sha256=target_hash,
        question_sha256=q_hash,
        prompt_template_sha256=prompt_tpl_hash,
        judge_model=judge_model,
        model_digest=m_digest,
        reason_sha256=hashlib.sha256(reason_str.encode("utf-8")).hexdigest(),
        supported=True,
        answer_grounded=True
    )

    expected_partition = assign_group_partition(row["filename"], row["page_num"])
    extracted_cand = {
        "source_id": f"src-pos-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": row["page_num"],
        "partition": expected_partition,
        "messages": msg,
        "review_evidence": {
            "judge_model": judge_model,
            "model_digest": m_digest,
            "supported": True,
            "answer_grounded": True,
            "reason": reason_str,
            "verdict_digest": verdict_hash,
            "source_sha256": src_hash,
            "target_sha256": target_hash,
            "prompt_template_sha256": prompt_tpl_hash,
            "evidence_spans": [safe_text[:35].strip()],
            "calibration_version": cur_mod.CALIBRATION_PROTOCOL_VERSION,
            "full_verdict": {
                "supported": True,
                "answer_grounded": True,
                "judge_model": judge_model,
                "model_digest": m_digest,
                "reason": reason_str,
                "unsupported_claims": [],
                "evidence_spans": [safe_text[:35].strip()],
                "source_sha256": src_hash,
                "target_sha256": target_hash,
                "question_sha256": q_hash,
                "prompt_template_sha256": prompt_tpl_hash,
                "calibration_version": cur_mod.CALIBRATION_PROTOCOL_VERSION,
                "verdict_digest": verdict_hash,
                "raw_response": {
                    "supported": True,
                    "answer_grounded": True,
                    "unsupported_claims": [],
                    "evidence_spans": [safe_text[:35].strip()],
                    "reason": reason_str
                }
            }
        }
    }

    # Add a canonical synthetic item in the other partition
    registry = get_synthetic_registry()
    canonical_syn = list(registry.values())[0]
    syn_partition = "valid" if expected_partition == "train" else "train"
    syn_cand = {
        "type": "synthetic_curriculum",
        "kind": canonical_syn["kind"],
        "facet": canonical_syn["facet"],
        "provenance": canonical_syn["provenance"],
        "derivation": canonical_syn["derivation"],
        "partition": syn_partition,
        "messages": canonical_syn["messages"],
        "review_evidence": {
            "supported": True,
            "answer_grounded": True,
            "verdict_digest": compute_review_verdict_digest(
                source_sha256=compute_digest(canonical_syn["derivation"]),
                target_sha256=compute_digest(canonical_syn["messages"]),
                question_sha256=compute_digest(canonical_syn["messages"][1]["content"]),
                prompt_template_sha256=hashlib.sha256(canonical_syn["provenance"].encode()).hexdigest(),
                judge_model="canonical_derivation_registry",
                model_digest=compute_digest(canonical_syn["derivation"]),
                reason_sha256=hashlib.sha256(canonical_syn["facet"].encode()).hexdigest(),
                supported=True,
                answer_grounded=True
            )
        }
    }

    (work_dir / "accepted.jsonl").write_text(
        json.dumps(extracted_cand) + "\n" + json.dumps(syn_cand) + "\n"
    )

    summary = publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=1, min_groups=1)
    assert publish_dir.exists()
    assert (publish_dir / "train.jsonl").exists()
    assert (publish_dir / "valid.jsonl").exists()
    assert (publish_dir / "approved_manifest.jsonl").exists()
    assert (publish_dir / "approval.json").exists()
    assert summary["dataset_sha256"] is not None


def test_reviewer_error_queued_as_pending_not_rejected(tmp_path, monkeypatch):
    """When judge fails with reviewer error (judge_call_failed), candidate must be queued in pending.jsonl, not rejected."""
    import app.curate_dataset_v7 as cur_mod

    work_dir = tmp_path / "work_pending_test"
    work_dir.mkdir()

    # Mock calibration
    monkeypatch.setattr(cur_mod, "ensure_judge_calibrated", lambda judge_model: {"all_passed": True})
    monkeypatch.setattr(cur_mod, "is_truncated_source_text", lambda text: False)

    # Mock teacher to succeed
    monkeypatch.setattr(cur_mod, "call_teacher_model", lambda src, facet, teacher_model: {
        "question": "Câu hỏi thử nghiệm?",
        "answer": "Câu trả lời thử nghiệm.",
        "claims": ["Luận điểm 1"]
    })

    # Mock judge to return reviewer failure
    monkeypatch.setattr(cur_mod, "call_judge_model", lambda src, cand, facet=None, judge_model="qwen2.5:7b", **kwargs: {
        "supported": False,
        "answer_grounded": False,
        "reason": "judge_call_failed",
        "judge_model": judge_model
    })

    chk = cur_mod.curate_candidates_workspace(work_dir, max_sources_to_curate=1)
    assert chk["pending_count"] == 1
    assert chk["rejected_count"] == 0

    pending_file = work_dir / "pending.jsonl"
    rejected_file = work_dir / "rejected.jsonl"
    assert pending_file.exists()
    pending_lines = [json.loads(l) for l in pending_file.read_text().splitlines() if l.strip()]
    assert len(pending_lines) == 1
    p_rec = pending_lines[0]
    assert p_rec["reason"] == "judge_call_failed"
    assert "context" in p_rec
    assert "target" in p_rec
    assert "question" in p_rec

    if rejected_file.exists():
        rej_lines = [l for l in rejected_file.read_text().splitlines() if l.strip()]
        assert len(rej_lines) == 0


def test_negative_full_verdict_under_positive_wrapper_rejected(tmp_path):
    """Probe: Gate must reject candidate if full_verdict.supported is False despite positive wrapper."""
    work_dir = tmp_path / "work_neg_fv"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_neg_fv"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, c.book_title, c.page_num FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    safe_text = sanitize_for_prompt_context(row["text"][:750])
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
    doc_header = f'<document id="S1" book="{row["book_title"]}" page="{row["page_num"]}">\n{safe_text}\n</document>'
    msg = [
        {"role": "system", "content": "Bạn là trợ lý tâm lý học."},
        {"role": "user", "content": f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: Nội dung?\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."},
        {"role": "assistant", "content": "Nội dung câu trả lời [S1]."}
    ]

    cand = {
        "source_id": f"src-neg-fv-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": row["page_num"],
        "partition": "train",
        "messages": msg,
        "review_evidence": {
            "judge_model": "qwen2.5:7b",
            "model_digest": get_ollama_model_digest("qwen2.5:7b"),
            "supported": True,
            "answer_grounded": True,
            "reason": "Wrapper lý do hợp lệ",
            "verdict_digest": "v_hash",
            "source_sha256": src_hash,
            "target_sha256": compute_digest(msg),
            "prompt_template_sha256": hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest(),
            "full_verdict": {
                "supported": False,  # Negative full verdict!
                "answer_grounded": False,
                "judge_model": "qwen2.5:7b",
                "reason": "Không đủ căn cứ",
                "unsupported_claims": ["claim1"]
            }
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="full_verdict.supported không phải boolean True hợp lệ"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_wrong_model_full_verdict_rejected(tmp_path):
    """Probe: Gate must reject candidate if full_verdict.judge_model mismatches review_evidence judge_model."""
    work_dir = tmp_path / "work_wrong_model"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_wrong_model"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, c.book_title, c.page_num FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    safe_text = sanitize_for_prompt_context(row["text"][:750])
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
    doc_header = f'<document id="S1" book="{row["book_title"]}" page="{row["page_num"]}">\n{safe_text}\n</document>'
    msg = [
        {"role": "system", "content": "Bạn là trợ lý tâm lý học."},
        {"role": "user", "content": f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: Nội dung?\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."},
        {"role": "assistant", "content": "Nội dung câu trả lời [S1]."}
    ]

    cand = {
        "source_id": f"src-wm-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": row["page_num"],
        "partition": "train",
        "messages": msg,
        "review_evidence": {
            "judge_model": "qwen2.5:7b",
            "model_digest": get_ollama_model_digest("qwen2.5:7b"),
            "supported": True,
            "answer_grounded": True,
            "reason": "Wrapper lý do hợp lệ",
            "verdict_digest": "v_hash",
            "source_sha256": src_hash,
            "target_sha256": compute_digest(msg),
            "prompt_template_sha256": hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest(),
            "full_verdict": {
                "supported": True,
                "answer_grounded": True,
                "judge_model": "qwen3:8b",  # Wrong model!
                "reason": "OK",
                "unsupported_claims": []
            }
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="judge_model trong full_verdict.*không khớp"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_missing_full_verdict_rejected(tmp_path):
    """Probe: Gate must reject candidate when full_verdict is completely absent."""
    work_dir = tmp_path / "work_missing_fv"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_missing_fv"

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, c.book_title, c.page_num FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    safe_text = sanitize_for_prompt_context(row["text"][:750])
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
    doc_header = f'<document id="S1" book="{row["book_title"]}" page="{row["page_num"]}">\n{safe_text}\n</document>'
    msg = [
        {"role": "system", "content": "Bạn là trợ lý tâm lý học."},
        {"role": "user", "content": f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: Nội dung?\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."},
        {"role": "assistant", "content": "Nội dung câu trả lời [S1]."}
    ]

    cand = {
        "source_id": f"src-mfv-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": row["page_num"],
        "partition": "train",
        "messages": msg,
        "review_evidence": {
            "judge_model": "qwen2.5:7b",
            "model_digest": get_ollama_model_digest("qwen2.5:7b"),
            "supported": True,
            "answer_grounded": True,
            "reason": "Wrapper lý do hợp lệ",
            "verdict_digest": "v_hash",
            "source_sha256": src_hash,
            "target_sha256": compute_digest(msg),
            "prompt_template_sha256": hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
            # full_verdict omitted!
        }
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="Thiếu hoặc sai định dạng full_verdict"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_get_ollama_model_digest_fail_closed_when_unavailable():
    """Fail-closed test: get_ollama_model_digest must raise RuntimeError for nonexistent model without default."""
    with pytest.raises(RuntimeError, match="CHẶN QUY TRÌNH: Không thể lấy model digest thực"):
        get_ollama_model_digest("nonexistent_model_xyz_99999")


# ---------------------------------------------------------------------------
# Codex Probes Remediation Suite (codex-bound-probes-2026-10-02-0250)
# ---------------------------------------------------------------------------

def _create_base_probe_candidate(db_path: Path):
    """Helper to create a structurally valid candidate with real DB chunk."""
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT c.id, c.text, c.filename, c.book_title, c.page_num FROM chunks c JOIN documents d ON c.doc_id = d.id "
            "WHERE c.filename NOT LIKE '%1241%' AND c.filename NOT LIKE '%dac_nhan_tam%' AND LENGTH(c.text) >= 150 LIMIT 1"
        ).fetchone()

    chunk_id = row["id"]
    from app.curate_dataset_v7 import extract_complete_source_text
    safe_text = extract_complete_source_text(row["text"], max_chars=900)
    src_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
    doc_header = f'<document id="S1" book="{row["book_title"]}" page="{row["page_num"]}">\n{safe_text}\n</document>'
    msg = [
        {"role": "system", "content": "Bạn là trợ lý tâm lý học."},
        {"role": "user", "content": f"<context>\n{doc_header}\n</context>\n\nCâu hỏi: Nội dung đoạn trích là gì?\nHãy trả lời chi tiết bằng tiếng Việt, dẫn mã [S1]."},
        {"role": "assistant", "content": "Nội dung câu trả lời hoàn toàn dựa vào đoạn trích [S1]."}
    ]
    target_hash = compute_digest(msg)
    q_hash = hashlib.sha256("Nội dung đoạn trích là gì?".encode("utf-8")).hexdigest()
    prompt_tpl_hash = hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
    judge_model = "qwen2.5:7b"
    m_digest = get_ollama_model_digest(judge_model)
    reason = "Lý giải thẩm định hợp lệ từ mô hình thẩm định viên"

    verdict_hash = compute_review_verdict_digest(
        source_sha256=src_hash,
        target_sha256=target_hash,
        question_sha256=q_hash,
        prompt_template_sha256=prompt_tpl_hash,
        judge_model=judge_model,
        model_digest=m_digest,
        reason_sha256=hashlib.sha256(reason.encode("utf-8")).hexdigest(),
        supported=True,
        answer_grounded=True
    )

    valid_span = safe_text[:30].strip()

    cand = {
        "source_id": f"src-probe-{chunk_id}",
        "chunk_id": chunk_id,
        "book": row["filename"],
        "page": row["page_num"],
        "partition": "train",
        "messages": msg,
        "review_evidence": {
            "judge_model": judge_model,
            "model_digest": m_digest,
            "supported": True,
            "answer_grounded": True,
            "reason": reason,
            "verdict_digest": verdict_hash,
            "source_sha256": src_hash,
            "target_sha256": target_hash,
            "prompt_template_sha256": prompt_tpl_hash,
            "evidence_spans": [valid_span],
            "calibration_version": CALIBRATION_PROTOCOL_VERSION,
            "full_verdict": {
                "supported": True,
                "answer_grounded": True,
                "judge_model": judge_model,
                "model_digest": m_digest,
                "reason": reason,
                "unsupported_claims": [],
                "evidence_spans": [valid_span],
                "source_sha256": src_hash,
                "target_sha256": target_hash,
                "question_sha256": q_hash,
                "prompt_template_sha256": prompt_tpl_hash,
                "calibration_version": CALIBRATION_PROTOCOL_VERSION,
                "verdict_digest": verdict_hash,
                "raw_response": {
                    "supported": True,
                    "answer_grounded": True,
                    "unsupported_claims": [],
                    "evidence_spans": [valid_span],
                    "reason": reason
                }
            }
        }
    }
    return cand, safe_text


def test_probe_baseline_missing_spans_and_raw_bindings_rejected(tmp_path):
    """Probe 1: Gate must reject candidate if full_verdict lacks evidence_spans and raw bindings."""
    work_dir = tmp_path / "work_p1"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p1"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    # Strip evidence_spans and raw bindings from full_verdict
    cand["review_evidence"]["full_verdict"] = {
        "supported": True,
        "answer_grounded": True,
        "judge_model": "qwen2.5:7b",
        "reason": cand["review_evidence"]["reason"],
        "unsupported_claims": []
        # missing evidence_spans, source_sha256, target_sha256, etc.
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="full_verdict thiếu evidence_spans"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_raw_binding_other_question_target_source_rejected(tmp_path):
    """Probe 2: Gate must reject candidate if full_verdict binds to another question/target/source."""
    work_dir = tmp_path / "work_p2"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p2"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    # Set mismatched source_sha256 in full_verdict
    cand["review_evidence"]["full_verdict"]["source_sha256"] = "other_source_hash_1234567890abcdef"
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="full_verdict source_sha256 không khớp"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_raw_model_digest_different_rejected(tmp_path):
    """Probe 3: Gate must reject candidate if full_verdict model_digest differs from released judge digest."""
    work_dir = tmp_path / "work_p3"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p3"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    cand["review_evidence"]["full_verdict"]["model_digest"] = "different_model_digest_999999999999"
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="full_verdict model_digest.*không khớp"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_fabricated_non_source_evidence_spans_rejected(tmp_path):
    """Probe 4: Gate must reject candidate if full_verdict evidence_spans contain non-source text."""
    work_dir = tmp_path / "work_p4"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p4"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    cand["review_evidence"]["full_verdict"]["evidence_spans"] = [
        "Cụm từ hoàn toàn bịa đặt và không hề tồn tại trong văn bản sách gốc"
    ]
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="evidence_span.*không tồn tại nguyên văn"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_raw_reason_differs_from_bound_wrapper_rejected(tmp_path):
    """Probe 5: Gate must reject candidate if raw full_verdict reason differs from bound wrapper reason."""
    work_dir = tmp_path / "work_p5"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_p5"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    cand["review_evidence"]["full_verdict"]["reason"] = "Lý do hoàn toàn khác biệt từ mô hình raw"
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="Lý giải.*trong full_verdict không khớp"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_production_parser_preserves_evidence_spans(monkeypatch):
    """Verify that call_judge_model parser preserves evidence_spans and all cryptographic bindings."""
    import app.curate_dataset_v7 as cur_mod

    mock_span = "quá trình học tập trong đó hành vi được củng cố"
    mock_response_content = json.dumps({
        "supported": True,
        "answer_grounded": True,
        "unsupported_claims": [],
        "evidence_spans": [mock_span],
        "reason": "Đầy đủ căn cứ khoa học từ trích đoạn"
    })

    class MockResponse:
        status_code = 200
        def json(self):
            return {"message": {"content": mock_response_content}}

    monkeypatch.setattr(cur_mod.requests, "post", lambda *a, **kw: MockResponse())
    monkeypatch.setattr(cur_mod, "get_ollama_model_digest", lambda m: "mock_model_digest_12345")

    src = {
        "chunk_id": 100,
        "book_title": "Sức mạnh của thói quen",
        "page_num": 10,
        "text": f"Theo Skinner, {mock_span} hoặc trừng phạt dựa trên hậu quả của nó."
    }
    cand = {
        "question": "Skinner định nghĩa điều kiện hóa như thế nào?",
        "answer": f"Theo Skinner, {mock_span} hoặc trừng phạt.",
        "claims": ["Luận điểm 1"]
    }

    result = cur_mod.call_judge_model(src, cand, facet="overview", judge_model="qwen2.5:7b")

    # Assert parser preserved evidence_spans and did not drop keys
    assert result["supported"] is True
    assert result["answer_grounded"] is True
    assert result["evidence_spans"] == [mock_span]
    assert result["source_sha256"] is not None
    assert result["target_sha256"] is not None
    assert result["question_sha256"] is not None
    assert result["model_digest"] == "mock_model_digest_12345"
    assert result["verdict_digest"] is not None
    assert result["prompt_template_sha256"] is not None


def test_probe_language_instruction_violation_rejected(tmp_path):
    """Gate must reject candidate answering in English when Vietnamese is requested."""
    work_dir = tmp_path / "work_lang"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_lang"

    cand, safe_text = _create_base_probe_candidate(DB_PATH)
    # Set English assistant response
    cand["messages"][2]["content"] = "Attachment theory posits that infants form emotional bonds with primary caregivers from early stages of life."
    # Update target hash and verdict digest
    cand["review_evidence"]["target_sha256"] = compute_digest(cand["messages"])
    cand["review_evidence"]["full_verdict"]["target_sha256"] = cand["review_evidence"]["target_sha256"]
    v_hash = compute_review_verdict_digest(
        source_sha256=cand["review_evidence"]["source_sha256"],
        target_sha256=cand["review_evidence"]["target_sha256"],
        question_sha256=cand["review_evidence"]["full_verdict"]["question_sha256"],
        prompt_template_sha256=cand["review_evidence"]["prompt_template_sha256"],
        judge_model=cand["review_evidence"]["judge_model"],
        model_digest=cand["review_evidence"]["model_digest"],
        reason_sha256=hashlib.sha256(cand["review_evidence"]["reason"].encode("utf-8")).hexdigest(),
        supported=True,
        answer_grounded=True
    )
    cand["review_evidence"]["verdict_digest"] = v_hash
    cand["review_evidence"]["full_verdict"]["verdict_digest"] = v_hash
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="tiếng Anh thay vì tiếng Việt"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_extract_complete_source_text_sentence_boundary():
    """Verify extract_complete_source_text produces clean sentences without mid-word or dangling punctuation slicing."""
    from app.curate_dataset_v7 import extract_complete_source_text, is_truncated_source_text

    raw = "Hệ thống 1 vận hành tự động và nhanh chóng. Hệ thống 2 phân bổ sự chú ý đến các hoạt động đòi hỏi nỗ lực trí tuệ. Đây là câu thứ ba trọn vẹn. Còn đây là câu bị cắt lửng giữa ch"
    extracted = extract_complete_source_text(raw, max_chars=120)
    assert not is_truncated_source_text(extracted)
    assert extracted.endswith(".")
    assert "Hệ thống 1" in extracted


def test_get_curation_sampled_sources_round_robin():
    """Verify get_curation_sampled_sources interleaves chunks across different books."""
    from app.curate_dataset_v7 import get_curation_sampled_sources
    with sqlite3.connect(DB_PATH) as db:
        sources = get_curation_sampled_sources(db, max_sources=15)
        books_seen = [s["filename"] for s in sources]
        # In a round-robin schedule across >= 3 books, adjacent elements should not all be the same book
        assert len(set(books_seen[:5])) >= 2


def test_probe_positive_control_with_nested_raw_response_passes(tmp_path, monkeypatch):
    """Gate must accept positive control candidate with matching valid nested raw_response and calibration version."""
    import app.curate_dataset_v7 as cur_mod
    monkeypatch.setattr(cur_mod, "audit_context_truncation", lambda staging_dir, max_seq_length: {"acceptable": True})

    work_dir = tmp_path / "work_pos_nested"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_pos_nested"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    summary = publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)
    assert summary["train_examples"] == 1
    assert summary["dataset_sha256"] is not None


def test_probe_negative_nested_raw_verdict_rejected(tmp_path):
    """Gate must reject candidate where envelope claims supported=True but nested raw_response is negative."""
    work_dir = tmp_path / "work_neg_raw"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_neg_raw"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    # Set nested raw_response to negative
    cand["review_evidence"]["full_verdict"]["raw_response"] = {
        "supported": False,
        "answer_grounded": False,
        "unsupported_claims": ["Luận điểm không có trong nguồn"],
        "reason": "Mô hình raw từ chối luận điểm"
    }
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="nested full_verdict.raw_response supported=False"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_missing_or_corrupted_raw_response_rejected(tmp_path):
    """Gate must reject candidate where nested raw_response is corrupted or invalid type."""
    work_dir = tmp_path / "work_corrupt_raw"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_corrupt_raw"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    cand["review_evidence"]["full_verdict"]["raw_response"] = "INVALID JSON {corrupted"
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="raw_response lỗi phân tích cú pháp JSON|raw_response không phải dict"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_missing_or_old_calibration_version_rejected(tmp_path):
    """Gate must reject candidate with obsolete calibration version."""
    work_dir = tmp_path / "work_old_calib"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_old_calib"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    cand["review_evidence"]["calibration_version"] = "v7.2_calibrated_bound_provenance"
    cand["review_evidence"]["full_verdict"]["calibration_version"] = "v7.2_calibrated_bound_provenance"
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="calibration_version không khớp hoặc bị thiếu"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_probe_unbound_cache_verdict_rejected():
    """is_valid_cached_judge_verdict must return False if any cryptographic binding is missing or mismatched."""
    source_text = "Nội dung văn bản nguồn kiểm thử trọn vẹn và hoàn chỉnh."
    question = "Câu hỏi thử nghiệm?"
    target_answer = "Câu trả lời thử nghiệm hoàn chỉnh."
    judge_model = "qwen2.5:7b"
    digest = get_ollama_model_digest(judge_model)
    prompt_tpl_hash = hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
    valid_span = source_text[:20]

    src_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    tgt_hash = hashlib.sha256(target_answer.strip().encode("utf-8")).hexdigest()
    q_hash = hashlib.sha256(question.strip().encode("utf-8")).hexdigest()

    valid_verdict = {
        "supported": True,
        "answer_grounded": True,
        "judge_model": judge_model,
        "model_digest": digest,
        "prompt_template_sha256": prompt_tpl_hash,
        "source_sha256": src_hash,
        "target_sha256": tgt_hash,
        "question_sha256": q_hash,
        "calibration_version": CALIBRATION_PROTOCOL_VERSION,
        "evidence_spans": [valid_span],
        "reason": "Hợp lệ đầy đủ",
        "raw_response": {
            "supported": True,
            "answer_grounded": True,
            "evidence_spans": [valid_span]
        }
    }

    # Baseline valid verdict passes
    assert is_valid_cached_judge_verdict(
        valid_verdict, source_text, question, target_answer,
        judge_model, digest, prompt_tpl_hash
    ) is True

    # Missing source_sha256 fails
    v_no_src = dict(valid_verdict, source_sha256=None)
    assert is_valid_cached_judge_verdict(v_no_src, source_text, question, target_answer, judge_model, digest, prompt_tpl_hash) is False

    # Missing target_sha256 fails
    v_no_tgt = dict(valid_verdict, target_sha256=None)
    assert is_valid_cached_judge_verdict(v_no_tgt, source_text, question, target_answer, judge_model, digest, prompt_tpl_hash) is False

    # Missing question_sha256 fails
    v_no_q = dict(valid_verdict, question_sha256=None)
    assert is_valid_cached_judge_verdict(v_no_q, source_text, question, target_answer, judge_model, digest, prompt_tpl_hash) is False

    # Old calibration version fails
    v_old_cal = dict(valid_verdict, calibration_version="v7.2_calibrated_bound_provenance")
    assert is_valid_cached_judge_verdict(v_old_cal, source_text, question, target_answer, judge_model, digest, prompt_tpl_hash) is False

    # Negative nested raw response fails
    v_neg_raw = dict(valid_verdict, raw_response={"supported": False})
    assert is_valid_cached_judge_verdict(v_neg_raw, source_text, question, target_answer, judge_model, digest, prompt_tpl_hash) is False


def test_probe_cache_verdict_with_changed_target_or_question_rejected():
    """is_valid_cached_judge_verdict must return False when target or question has changed."""
    source_text = "Nội dung văn bản nguồn kiểm thử trọn vẹn và hoàn chỉnh."
    question = "Câu hỏi ban đầu?"
    target_answer = "Câu trả lời ban đầu."
    judge_model = "qwen2.5:7b"
    digest = get_ollama_model_digest(judge_model)
    prompt_tpl_hash = hashlib.sha256(JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
    valid_span = source_text[:20]

    src_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    tgt_hash = hashlib.sha256(target_answer.strip().encode("utf-8")).hexdigest()
    q_hash = hashlib.sha256(question.strip().encode("utf-8")).hexdigest()

    cached_verdict = {
        "supported": True,
        "answer_grounded": True,
        "judge_model": judge_model,
        "model_digest": digest,
        "prompt_template_sha256": prompt_tpl_hash,
        "source_sha256": src_hash,
        "target_sha256": tgt_hash,
        "question_sha256": q_hash,
        "calibration_version": CALIBRATION_PROTOCOL_VERSION,
        "evidence_spans": [valid_span],
        "reason": "Hợp lệ",
        "raw_response": {"supported": True, "answer_grounded": True, "evidence_spans": [valid_span]}
    }

    # Changed question -> False
    assert is_valid_cached_judge_verdict(
        cached_verdict, source_text, "Câu hỏi đã bị sửa đổi?", target_answer,
        judge_model, digest, prompt_tpl_hash
    ) is False

    # Changed target answer -> False
    assert is_valid_cached_judge_verdict(
        cached_verdict, source_text, question, "Câu trả lời đã bị sửa đổi hoàn toàn.",
        judge_model, digest, prompt_tpl_hash
    ) is False


def test_probe_corrupted_or_non_string_evidence_spans_rejected(tmp_path):
    """Gate must reject candidate if evidence_spans contains non-string, empty or non-source elements."""
    work_dir = tmp_path / "work_bad_spans"
    work_dir.mkdir()
    publish_dir = tmp_path / "v7_bad_spans"

    cand, _ = _create_base_probe_candidate(DB_PATH)
    # Empty string span
    cand["review_evidence"]["full_verdict"]["evidence_spans"] = ["   "]
    (work_dir / "accepted.jsonl").write_text(json.dumps(cand) + "\n")

    with pytest.raises(ValueError, match="evidence_spans chứa phần tử rỗng|không tồn tại nguyên văn"):
        publish_v7_dataset(work_dir, publish_dir, min_train=1, min_valid=0, min_groups=1)


def test_curation_cache_hit_validates_judge_verdict(tmp_path, monkeypatch):
    """Curation workspace must validate cached judge verdicts and rejudge if invalid."""
    import app.curate_dataset_v7 as cur_mod

    work_dir = tmp_path / "work_cache_val"
    work_dir.mkdir()

    # Mock calibration
    monkeypatch.setattr(cur_mod, "ensure_judge_calibrated", lambda judge_model: {"all_passed": True})
    monkeypatch.setattr(cur_mod, "is_truncated_source_text", lambda text: False)

    mock_q = "Skinner giải thích hành vi như thế nào?"
    mock_a = "Skinner giải thích hành vi qua điều kiện hóa thao tác."

    monkeypatch.setattr(cur_mod, "call_teacher_model", lambda src, facet, teacher_model: {
        "question": mock_q,
        "answer": mock_a,
        "claims": ["Luận điểm 1"]
    })

    judge_call_count = [0]
    def mock_judge(src, cand, facet="fact_recall", judge_model="qwen2.5:7b", **kwargs):
        judge_call_count[0] += 1
        return {
            "supported": True,
            "answer_grounded": True,
            "reason": "Thẩm định viên hợp lệ gọi thực",
            "evidence_spans": [src["text"][:20].strip()],
            "unsupported_claims": [],
            "judge_model": judge_model,
            "model_digest": get_ollama_model_digest(judge_model),
            "source_sha256": hashlib.sha256(src["text"].encode("utf-8")).hexdigest(),
            "target_sha256": hashlib.sha256(cand["answer"].encode("utf-8")).hexdigest(),
            "question_sha256": hashlib.sha256(cand["question"].encode("utf-8")).hexdigest(),
            "prompt_template_sha256": hashlib.sha256(cur_mod.JUDGE_PROMPT_TEMPLATE.encode("utf-8")).hexdigest(),
            "calibration_version": cur_mod.CALIBRATION_PROTOCOL_VERSION,
            "raw_response": {"supported": True, "answer_grounded": True, "evidence_spans": [src["text"][:20].strip()]}
        }

    monkeypatch.setattr(cur_mod, "call_judge_model", mock_judge)

    # Prepopulate cache with an INVALID cached judge verdict (negative nested raw_response)
    cache_file = work_dir / "cache.json"
    dummy_source = {"text": "Theo Skinner, điều kiện hóa thao tác củng cố hành vi."}
    cache_key = cur_mod.compute_curation_cache_key(
        dummy_source["text"][:750], "overview", "qwen2.5:7b", "qwen2.5:7b",
        cur_mod.TEACHER_PROMPT_TEMPLATE, cur_mod.JUDGE_PROMPT_TEMPLATE,
        teacher_model_digest=get_ollama_model_digest("qwen2.5:7b"),
        judge_model_digest=get_ollama_model_digest("qwen2.5:7b")
    )
    corrupted_cache = {
        cache_key: {
            "candidate": {"question": mock_q, "answer": mock_a, "claims": ["Luận điểm 1"]},
            # Corrupted judge verdict lacking bindings and with negative nested raw response
            "judge": {
                "supported": True,
                "answer_grounded": True,
                "raw_response": {"supported": False}
            }
        }
    }
    cache_file.write_text(json.dumps(corrupted_cache))

    # Mock get_curation_sampled_sources to return 1 item matching dummy_source
    monkeypatch.setattr(cur_mod, "get_curation_sampled_sources", lambda db, *args, **kwargs: [
        {"id": "src-1", "chunk_id": 1, "filename": "5446-suc-manh-cua-thoi-quen.pdf", "page_num": 1, "book_title": "Thói quen", "text": dummy_source["text"], "partition": "train"}
    ])

    chk = cur_mod.curate_candidates_workspace(work_dir, max_sources_to_curate=1)
    # Judge MUST have been called because cached verdict failed validation
    assert judge_call_count[0] == 1


def test_is_substantive_psychology_source_rejects_credits_and_boilerplate():
    """Verify source eligibility filter blocks editorial credits, publisher history, TOC, and truncated text."""
    # Chunk 37524: Editorial staff credits
    credits_chunk = (
        "Vice-President, Editorial Director: Gary Bennett\n"
        "Editor-in-Chief: Michelle Sartor\n"
        "Acquisitions Editor: Matthew Christian\n"
        "Marketing Manager: Lisa Gillis\n"
        "Supervising Developmental Editor: Maurice Esses\n"
        "Developmental Editor: Cindy Miller, Element LLC"
    )
    is_sub, reason = is_substantive_psychology_source(credits_chunk)
    assert is_sub is False
    assert "editorial_staff" in reason

    # Chunk 46162: Publisher corporate history boilerplate
    boilerplate_chunk = (
        "W. W. NORTON & COMPANY has been independent since its founding in 1923, "
        "when William Warder Norton and Mary D. Herter Norton first published lectures. "
        "W. W. Norton & Company stands as the largest and oldest publishing house owned wholly by its employees. "
        "Copyright © 2022 by W."
    )
    is_sub, reason = is_substantive_psychology_source(boilerplate_chunk)
    assert is_sub is False
    assert "publisher_cataloging" in reason or "boilerplate" in reason

    # Table of contents
    toc_chunk = (
        "Brief Contents\n"
        "1 ■ Introduction to Clinical Case Presentations 3\n"
        "2 ■ Neuroanatomy Overview and Basic Definitions 13\n"
        "3 ■ The Neurologic Exam as a Lesson in Neuroanatomy 49\n"
        "4 ■ Introduction to Clinical Neuroradiology 85"
    )
    is_sub, reason = is_substantive_psychology_source(toc_chunk)
    assert is_sub is False

    # Contributor biography (e.g. Meagher 44527)
    bio_chunk = (
        "Handbook of Thanatology\n"
        "xvi\n"
        "Alicia Skinner Cook, PhD, is a licensed psychologist and professor emeritus in the "
        "Department of Human Development and Family Studies at Colorado State University.\n\n"
        "Cook’s scholarly work has focused on families and grief and the ethics of conducting "
        "bereavement research.\n\n"
        "She has published more than 45 articles and four books and has "
        "been a visiting scholar at the Hastings Center for Biomedical Ethics."
    )
    is_sub, reason = is_substantive_psychology_source(bio_chunk)
    assert is_sub is False
    assert "contributor_biography" in reason

    # Acknowledgements boilerplate (e.g. Howell 49937)
    ack_chunk = (
        "Acknowledgements\n"
        "Putting together this co-edited book has been a labor of love and a meaningful "
        "opportunity to wrestle with important issues relating to the emerging "
        "field of trauma-generated dissociation."
    )
    is_sub, reason = is_substantive_psychology_source(ack_chunk)
    assert is_sub is False
    assert "acknowledgements" in reason

    # Substantive psychology excerpt
    substantive_chunk = (
        "Chương này giới thiệu những vấn đề của tâm lí học dị thường, trong đó có nhiều vấn đề được bàn sâu ở các phần sau. "
        "Bắt đầu bằng khái niệm về tâm lí học dị thường và nó liên quan như thế nào đến sức khoẻ tâm thần (SKTT); "
        "sự thay đổi quan niệm qua từng thời kì trước khi xem xét đến các cách thức hình thành những vấn đề về SKTT."
    )
    is_sub, reason = is_substantive_psychology_source(substantive_chunk)
    assert is_sub is True
    assert reason == ""


def test_resolve_exact_source_span_offsets():
    """Verify whitespace-insensitive span resolver extracts verbatim slices and offsets without permitting altered words."""
    source_text = (
        "Chương này giới thiệu những vấn đề của tâm lí học dị thường, trong đó có nhiều vấn\n"
        "đề được bàn sâu ở các phần sau. Bắt đầu bằng khái niệm về tâm lí học dị thường và nó liên\n"
        "quan như thế nào đến sức khoẻ tâm thần."
    )
    # Candidate span has space where source has newline (\n)
    candidate_span = "trong đó có nhiều vấn đề được bàn sâu ở các phần sau."
    res = resolve_exact_source_span_offsets(source_text, candidate_span)
    assert res is not None
    verbatim_slice, start, end = res
    assert verbatim_slice == "trong đó có nhiều vấn\nđề được bàn sâu ở các phần sau."
    assert source_text[start:end] == verbatim_slice
    assert start > 0 and end > start

    # Positive: Curly quotes in source vs straight quotes in candidate
    curly_source = 'hành động diễn ra lúc “tắm”, khi ngâm dung dịch.'
    straight_cand = 'hành động diễn ra lúc "tắm", khi ngâm dung dịch.'
    res_q = resolve_exact_source_span_offsets(curly_source, straight_cand)
    assert res_q is not None
    assert res_q[0] == curly_source

    # Negative: Altered word must NOT match
    altered_span = "trong đó có nhiều vấn nạn được bàn sâu ở các phần sau."
    assert resolve_exact_source_span_offsets(source_text, altered_span) is None

    # Negative: Missing word must NOT match
    dropped_span = "trong đó nhiều vấn đề được bàn sâu ở các phần sau."
    assert resolve_exact_source_span_offsets(source_text, dropped_span) is None

    # Negative: Translated span must NOT match
    translated_span = "in which there are many issues discussed deeply in later sections."
    assert resolve_exact_source_span_offsets(source_text, translated_span) is None


def test_validate_and_parse_judge_verdict_with_whitespace_span_mapping():
    """Verify validate_and_parse_judge_verdict accepts spans matching across newlines and returns offsets."""
    source_text = (
        "Theo Skinner, điều kiện hóa thao tác là một quá trình học tập trong đó hành vi\n"
        "được củng cố hoặc trừng phạt dựa trên hậu quả của nó."
    )
    # Span has space instead of newline
    span_with_space = "quá trình học tập trong đó hành vi được củng cố"
    raw_payload = {
        "supported": True,
        "answer_grounded": True,
        "unsupported_claims": [],
        "evidence_spans": [span_with_space],
        "reason": "Đầy đủ căn cứ từ nguồn trích."
    }
    verdict = validate_and_parse_judge_verdict(
        raw_payload=raw_payload,
        source_text=source_text,
        question="Điều kiện hóa thao tác là gì?",
        target_answer="Theo đoạn trích [S1], điều kiện hóa thao tác là quá trình học tập trong đó hành vi được củng cố [S1].",
        judge_model="qwen2.5:7b",
        model_digest="mock_digest_123",
        prompt_template_sha256="mock_prompt_sha",
        require_citation=True
    )
    assert verdict["supported"] is True
    assert verdict["answer_grounded"] is True
    # The evidence_spans must contain the verbatim slice with newline
    assert "quá trình học tập trong đó hành vi\nđược củng cố" in verdict["evidence_spans"]
    assert len(verdict["evidence_span_offsets"]) == 1
    assert verdict["evidence_span_offsets"][0]["start"] > 0
    assert verdict["evidence_span_offsets"][0]["end"] > verdict["evidence_span_offsets"][0]["start"]


def test_metadata_as_reasoning_negative_control_rejected():
    """Negative control: Metadata/credits source with conditional reasoning claims must fail validation."""
    source_text = (
        "Vice-President, Editorial Director: Gary Bennett\n"
        "Editor-in-Chief: Michelle Sartor\n"
        "Acquisitions Editor: Matthew Christian\n"
        "Marketing Manager: Lisa Gillis\n"
        "Supervising Developmental Editor: Maurice Esses\n"
        "Copyright © 2014 by Pearson Education, Inc."
    )
    raw_payload = {
        "supported": True,  # Raw judge hallucinates support
        "answer_grounded": True,
        "unsupported_claims": [],
        "evidence_spans": ["Vice-President, Editorial Director: Gary Bennett"],
        "reason": "Cấu trúc ban biên tập chứng minh conditional reasoning."
    }
    verdict = validate_and_parse_judge_verdict(
        raw_payload=raw_payload,
        source_text=source_text,
        question="Cấu trúc ban biên tập phản ánh suy luận điều kiện như thế nào?",
        target_answer="Đoạn trích [S1] chứng minh quy trình xuất bản áp dụng conditional reasoning [S1].",
        judge_model="qwen2.5:7b",
        model_digest="mock_digest_123",
        prompt_template_sha256="mock_prompt_sha",
        require_citation=True
    )
    # Must fail because source is non-substantive editorial credits
    assert verdict["supported"] is False
    assert any("ineligible_source" in c for c in verdict["unsupported_claims"])


def test_real_wrapped_source_with_newlines_positive_control():
    """Positive control: Real excerpt with OCR newlines and grounded answer passes validation."""
    source_text = (
        "Hiệu ứng mỏ neo xuất hiện khi người ta cân nhắc một giá trị cụ thể cho một đại lượng\n"
        "chưa biết trước khi ước tính đại lượng đó. Những ước tính vẫn duy trì ở gần con số\n"
        "mà mọi người đã cân nhắc trước đó."
    )
    raw_payload = {
        "supported": True,
        "answer_grounded": True,
        "unsupported_claims": [],
        "evidence_spans": ["Hiệu ứng mỏ neo xuất hiện khi người ta cân nhắc một giá trị cụ thể"],
        "reason": "Hoàn toàn phù hợp với nguồn trích."
    }
    verdict = validate_and_parse_judge_verdict(
        raw_payload=raw_payload,
        source_text=source_text,
        question="Hiệu ứng mỏ neo xuất hiện như thế nào?",
        target_answer="Theo đoạn trích [S1], hiệu ứng mỏ neo xuất hiện khi người ta cân nhắc một giá trị cụ thể trước khi ước tính [S1].",
        judge_model="qwen2.5:7b",
        model_digest="mock_digest_123",
        prompt_template_sha256="mock_prompt_sha",
        require_citation=True
    )
    assert verdict["supported"] is True
    assert len(verdict["evidence_spans"]) == 1
    assert verdict["evidence_span_offsets"][0]["start"] == 0


def test_missing_s1_citation_rejected_when_required():
    """Verify that candidate answers lacking [S1] citation are rejected when require_citation=True."""
    source_text = (
        "Theo Skinner, điều kiện hóa thao tác là một quá trình học tập trong đó hành vi "
        "được củng cố hoặc trừng phạt dựa trên hậu quả của nó."
    )
    raw_payload = {
        "supported": True,
        "answer_grounded": True,
        "unsupported_claims": [],
        "evidence_spans": ["quá trình học tập trong đó hành vi được củng cố"],
        "reason": "Hoàn toàn có căn cứ."
    }
    # Answer completely lacks [S1]
    answer_no_citation = "Theo Skinner, điều kiện hóa thao tác là một quá trình học tập củng cố hành vi."
    verdict = validate_and_parse_judge_verdict(
        raw_payload=raw_payload,
        source_text=source_text,
        question="Điều kiện hóa thao tác là gì?",
        target_answer=answer_no_citation,
        judge_model="qwen2.5:7b",
        model_digest="mock_digest_123",
        prompt_template_sha256="mock_prompt_sha",
        require_citation=True
    )
    assert verdict["supported"] is False
    assert "missing_s1_citation" in verdict["unsupported_claims"]


def test_resolve_exact_source_span_offsets_strict_case():
    """Case changes must fail to resolve (US vs us must return None)."""
    source_text = "The US is mentioned in the cognitive psychology research."
    case_altered_span = "The us is mentioned in the cognitive psychology research."
    assert resolve_exact_source_span_offsets(source_text, case_altered_span) is None
    # Exact case matches
    assert resolve_exact_source_span_offsets(source_text, "The US is mentioned") is not None


def test_truncate_to_sentence_boundary_no_synthetic_period():
    """Text without terminal punctuation must not have a synthetic period appended."""
    text_without_punct = "Đây là một đoạn văn dài mà không hề có dấu chấm kết thúc câu ở bất cứ đâu trong toàn bộ nội dung"
    truncated = truncate_to_sentence_boundary(text_without_punct, max_chars=50)
    assert not truncated.endswith(".")
    assert is_truncated_source_text(truncated) is True


def test_segment_text_into_sentences():
    """Segment text into ordered sentences with verbatim start/end offsets and abbreviation protection."""
    src = "Dr. Smith presented the study at 2 p.m. The results confirmed hypothesis A! Did everyone agree? Yes, they did."
    sents = segment_text_into_sentences(src, prefix="S1")
    assert len(sents) == 4
    assert sents[0]["id"] == "S1.1"
    assert "Dr. Smith presented the study at 2 p.m." in sents[0]["text"]
    assert src[sents[0]["start"]:sents[0]["end"]].strip() == sents[0]["text"]
    assert sents[1]["id"] == "S1.2"
    assert sents[2]["id"] == "S1.3"
    assert sents[3]["id"] == "S1.4"


def test_validate_claim_map_full_coverage():
    """Verify 100% claim-to-sentence coverage passes validation."""
    source_text = "Tâm lý học nhận thức nghiên cứu các quá trình tư duy. Trí nhớ là một cấu phần then chốt."
    answer = "Tâm lý học nhận thức tập trung vào quá trình tư duy. Trí nhớ giữ vai trò trung tâm trong nhận thức [S1]."
    
    src_sents = segment_text_into_sentences(source_text, prefix="S1")
    ans_sents = segment_text_into_sentences(answer, prefix="A1")
    
    claim_map = [
        {
            "claim_id": "C1",
            "claim_text": "Tâm lý học nhận thức tập trung vào tư duy",
            "answer_sentence_id": ans_sents[0]["id"],
            "answer_offsets": [ans_sents[0]["start"], ans_sents[0]["end"]],
            "source_id": "S1",
            "source_sentence_ids": ["S1.1"],
            "evidence_spans": ["Tâm lý học nhận thức nghiên cứu các quá trình tư duy."],
            "relation": "entailment",
            "modality": "asserted",
            "claim_type": "fact",
            "is_supported": True
        },
        {
            "claim_id": "C2",
            "claim_text": "Trí nhớ là cấu phần trung tâm",
            "answer_sentence_id": ans_sents[1]["id"],
            "answer_offsets": [ans_sents[1]["start"], ans_sents[1]["end"]],
            "source_id": "S1",
            "source_sentence_ids": ["S1.2"],
            "evidence_spans": ["Trí nhớ là một cấu phần then chốt."],
            "relation": "entailment",
            "modality": "asserted",
            "claim_type": "fact",
            "is_supported": True
        }
    ]
    
    res = validate_claim_map(source_text, answer, claim_map, source_id="S1")
    assert res["valid"] is True
    assert res["coverage"] == 1.0
    assert len(res["violations"]) == 0


def test_validate_claim_map_incomplete_coverage_blocked():
    """Missing coverage on any answer sentence blocks approval fail-closed."""
    source_text = "Tâm lý học nhận thức nghiên cứu các quá trình tư duy."
    answer = "Câu thứ nhất đã được lập luận [S1]. Nhưng câu thứ hai hoàn toàn không có claim bảo chứng."
    
    ans_sents = segment_text_into_sentences(answer, prefix="A1")
    
    claim_map = [
        {
            "claim_id": "C1",
            "claim_text": "Câu thứ nhất được lập luận",
            "answer_sentence_id": ans_sents[0]["id"],
            "answer_offsets": [ans_sents[0]["start"], ans_sents[0]["end"]],
            "source_id": "S1",
            "source_sentence_ids": ["S1.1"],
            "evidence_spans": ["Tâm lý học nhận thức nghiên cứu các quá trình tư duy."],
            "relation": "entailment",
            "modality": "asserted",
            "claim_type": "fact",
            "is_supported": True
        }
    ]
    
    res = validate_claim_map(source_text, answer, claim_map, source_id="S1")
    assert res["valid"] is False
    assert res["coverage"] < 1.0
    assert any("incomplete_answer_coverage" in v for v in res["violations"])


def test_validate_and_parse_judge_verdict_done_reason_length_fail_closed():
    """Verdict must fail-closed if done_reason == 'length'."""
    source_text = "Nghiên cứu về điều kiện hóa hành vi của Skinner."
    raw_payload = {
        "supported": True,
        "answer_grounded": True,
        "unsupported_claims": [],
        "evidence_spans": ["Nghiên cứu về điều kiện hóa hành vi của Skinner."],
        "reason": "Đầy đủ bằng chứng."
    }
    verdict = validate_and_parse_judge_verdict(
        raw_payload=raw_payload,
        source_text=source_text,
        question="Skinner nghiên cứu gì?",
        target_answer="Skinner nghiên cứu điều kiện hóa hành vi [S1].",
        judge_model="qwen2.5:7b",
        model_digest="mock_digest_123",
        prompt_template_sha256="mock_prompt_sha",
        done_reason="length"
    )
    assert verdict["supported"] is False
    assert "generation_truncated_length" in verdict["unsupported_claims"]


