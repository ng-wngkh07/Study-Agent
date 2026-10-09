"""Independent contract probes for resource safety and OCR/training integrity."""
from pathlib import Path
import json
import sys
from types import SimpleNamespace

from app.config import MLX_MODEL_DIR
from app import memory_preflight as memory
from app import vision_ocr
from app import token_auditor


def test_unknown_available_memory_cannot_authorize_training(monkeypatch):
    monkeypatch.setattr(memory, "get_hardware_memory_profile", lambda: {
        "eligible": True, "measurement_error": None, "total_gb": 16,
        "available_gb": None, "disk_free_gb": 100,
        "swap_used_mb": 0, "wired_gb": 2,
    })
    result = memory.preflight_check_memory_training(
        model_dir=MLX_MODEL_DIR, num_layers=2, max_seq_length=512)
    assert result["eligible_for_training"] is False


def test_real_macos_swap_format_is_measured(monkeypatch):
    def measured_output(command, **kwargs):
        if "hw.memsize" in command:
            return "17179869184\n"
        if "vm.swapusage" in command:
            return "vm.swapusage: total = 6144.00M  used = 2311.50M  free = 3832.50M  (encrypted)\n"
        if command[0] == "vm_stat":
            return ("Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
                    "Pages free: 204800.\nPages inactive: 81920.\n"
                    "Pages active: 200000.\nPages wired down: 131072.\n")
        raise OSError("Unsupported measurement in isolated fixture")
    monkeypatch.setattr(memory.subprocess, "check_output", measured_output)
    result = memory.get_hardware_memory_profile()
    assert result["swap_used_mb"] == 2311.5
    assert result["swap_total_mb"] == 6144


class ExactCharacterFixture:
    """A known tokenizer fixture; one Unicode character is exactly one token."""
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        text = "".join("[" + m["role"] + "]" + m["content"] for m in messages)
        return list(text) if tokenize else text

    def encode(self, text, **kwargs):
        return list(text)


def audit_fixture(tmp_path, monkeypatch, records, valid_records=None, max_seq_length=30):
    tokenizer = ExactCharacterFixture()
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a, **k: tokenizer)))
    model_dir = tmp_path / "base"
    model_dir.mkdir()
    for name, data in [("train", records), ("valid", records if valid_records is None else valid_records)]:
        (tmp_path / (name + ".jsonl")).write_text("\n".join(json.dumps(x) for x in data))
    return token_auditor._run_exact_audit_local(tmp_path, model_dir, max_seq_length)


def test_even_one_truncated_record_is_rejected(tmp_path, monkeypatch):
    short = {"messages": [{"role": "user", "content": "q"},
                          {"role": "assistant", "content": "a"}]}
    long = {"messages": [{"role": "user", "content": "q"},
                         {"role": "assistant", "content": "z" * 100}]}
    result = audit_fixture(tmp_path, monkeypatch, [short] * 99 + [long], [short])
    assert result["has_violations"] is True
    assert any(v["code"] == "MAX_SEQ_LENGTH_EXCEEDED" for v in result["violations"])


def test_empty_training_split_is_rejected(tmp_path, monkeypatch):
    valid = {"messages": [{"role": "user", "content": "q"},
                          {"role": "assistant", "content": "a"}]}
    result = audit_fixture(tmp_path, monkeypatch, [], [valid])
    assert result["has_violations"] is True


def test_masked_prompt_record_must_end_with_assistant(tmp_path, monkeypatch):
    record = {"messages": [{"role": "user", "content": "q"},
                           {"role": "assistant", "content": "a"},
                           {"role": "user", "content": "q"}]}
    result = audit_fixture(tmp_path, monkeypatch, [record])
    assert result["has_violations"] is True


def test_non_string_targets_are_not_coerced_to_training_text(tmp_path, monkeypatch):
    result = audit_fixture(tmp_path, monkeypatch, [{"prompt": None, "completion": None}])
    assert result["has_violations"] is True


def test_unverified_vision_ocr_cannot_enter_training():
    allowed, reason = vision_ocr.VisionOCRManager.is_allowed_in_training({
        "backend": "ollama_vision", "ocr_type": "vision_llm",
        "is_verified": False, "needs_review": False,
        "handwriting_suspected": False, "text": "A plausible but unchecked transcription",
    })
    assert allowed is False


def test_ocr_cache_key_cannot_escape_cache_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(vision_ocr, "CACHE_DIR", tmp_path / "cache")
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps({"text": "do not change"}))
    try:
        vision_ocr.VisionOCRManager.review_and_verify_transcript(
            "../outside", "changed", "reviewer")
    except (ValueError, FileNotFoundError):
        pass
    else:
        raise AssertionError("A review accepted a cache path outside its directory")
    assert json.loads(outside.read_text())["text"] == "do not change"


def test_word_overlap_cannot_certify_a_contradictory_answer():
    from app.paired_evaluation import evaluate_passage_grounding
    passage = "Một cơ sở của không gian vectơ V phải là một tập sinh của V và độc lập tuyến tính."
    answer = "[S1] Một cơ sở của không gian vectơ V chỉ cần là một tập sinh của V và không cần độc lập tuyến tính."
    result = evaluate_passage_grounding(answer, passage)
    assert result.get("is_grounded") is not True


def test_refusal_keyword_cannot_certify_an_unsupported_claim():
    from app.paired_evaluation import evaluate_passage_grounding
    answer = "Tài liệu không đề cập, nhưng tác giả đã chứng minh thuốc này chữa được mọi bệnh."
    result = evaluate_passage_grounding(answer, "", is_no_source_expected=True)
    assert result.get("is_grounded") is not True


def test_brief_native_pdf_is_readable_without_ocr(tmp_path):
    import pymupdf
    from app.pdf_extractor import PDFExtractor
    file = tmp_path / "brief.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((30, 40), "A basis is a linearly independent spanning set. This page contains native readable text.")
    doc.save(file)
    doc.close()
    result = PDFExtractor.extract_pdf(file)
    assert result.extracted_pages[0]["has_text"] is True
    assert result.is_scanned is False


def test_unreadable_dataset_still_has_durable_terminal_attempt(tmp_path, monkeypatch):
    from app import fine_tune
    calls = []

    class AttemptLedger:
        def create_run(self, **kwargs):
            calls.append(("create", kwargs))
            return {"run_id": "isolated-attempt"}

        def update_status(self, run_id, status, **kwargs):
            calls.append((status, kwargs))

    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "train.jsonl").write_text('{}\n')
    (dataset / "valid.jsonl").write_text('{}\n')
    original_read = Path.read_text

    def deny_train_read(path, *args, **kwargs):
        if path == dataset / "train.jsonl":
            raise PermissionError("isolated unreadable training source")
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny_train_read)
    monkeypatch.setattr(fine_tune.subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("unreadable data must not spawn training")))
    import pytest
    with pytest.raises(PermissionError):
        fine_tune.train(dataset, model_dir=tmp_path / "base", ledger=AttemptLedger())
    assert calls and calls[0][0] == "create", "allocate an attempt before reading data"
    assert any(status in {"REJECTED", "FAILED"} for status, _ in calls[1:])


def test_unreviewed_paired_outputs_cannot_pass_promotion_gates():
    from app.paired_evaluation import evaluate_paired_dossier
    passage = "Một cơ sở là một tập sinh độc lập tuyến tính."
    cases = [{"id": "independent-target", "category": "targeted_repair", "passage": passage}]
    result = evaluate_paired_dossier(cases, ["Sai"], ["[S1] " + passage])
    assert not any(value is True for value in result.get("gates", {}).values()), (
        "lexical diagnostics without bound semantic review must fail closed")


def test_paired_evidence_keeps_exact_source_and_outputs():
    from app.paired_evaluation import evaluate_paired_dossier
    cases = [{"id": "retention-1", "category": "retention_benchmark", "passage": "Nguồn độc lập."}]
    base, candidate = "Bản nền có lỗi riêng.", "Ứng viên có lỗi khác."
    serialized = json.dumps(evaluate_paired_dossier(cases, [base], [candidate]), ensure_ascii=False)
    assert all(value in serialized for value in (base, candidate, cases[0]["passage"]))


def test_verified_flag_without_bound_claim_reviews_cannot_promote():
    from app.paired_evaluation import evaluate_paired_dossier
    passage = "Một cơ sở là một tập sinh độc lập tuyến tính."
    cases = [{"id": "target-1", "category": "targeted_repair", "passage": passage,
              "semantic_review": {"is_verified": True, "reviewer": "Codex"}}]
    result = evaluate_paired_dossier(cases, ["Sai"], ["[S1] " + passage])
    assert not any(value is True for value in result.get("gates", {}).values()), (
        "a reviewer flag without grades, reasons and exact output/source hashes is not a review")


def test_adapter_registry_rejects_acceptance_flags_without_evidence(tmp_path):
    from app.active_registry import ActiveAdapterRegistry
    import pytest
    registry = ActiveAdapterRegistry(tmp_path / "active.json")
    adapter = tmp_path / "candidate"
    adapter.mkdir()
    (adapter / "adapters.safetensors").write_bytes(b"isolated-unreviewed-weights")
    with pytest.raises(ValueError):
        registry.promote_adapter("unreviewed", adapter, {
            "semantically_accepted": True, "reviewed_by_codex": True,
        })
    assert registry.get_active_adapter_dir() is None


def test_legacy_ready_marker_does_not_select_an_unaccepted_adapter(tmp_path, monkeypatch):
    from app import trained_client
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "ready.json").write_text('{}')
    (legacy / "adapters.safetensors").write_bytes(b"isolated-legacy")
    monkeypatch.setattr(trained_client, "MLX_ADAPTER_DIR", legacy)
    monkeypatch.setattr(trained_client.TrainedModelClient, "_verify_legacy_adapter", staticmethod(lambda p: True), raising=False)
    monkeypatch.setattr(trained_client, "active_registry", SimpleNamespace(get_active_adapter_dir=lambda: None))
    captured = []

    def infer(*args, **kwargs):
        captured.append(json.loads(kwargs["input"]))
        return SimpleNamespace(returncode=0, stdout=json.dumps({"answer": "fixture", "is_truncated": False}))

    monkeypatch.setattr(trained_client.subprocess, "run", infer)
    list(trained_client.TrainedModelClient().chat_stream([{"role":"user","content":"probe"}]))
    assert captured[0]["adapter_path"] is None, "only a bound accepted registry may select an adapter"


def test_candidate_only_review_cannot_claim_paired_improvement():
    import hashlib
    from app.paired_evaluation import evaluate_paired_dossier
    answer = "Một cơ sở là một tập sinh độc lập tuyến tính."
    h = hashlib.sha256(answer.encode()).hexdigest()
    case = {"id":"same-correct-answer", "category":"targeted_repair", "passage":answer,
            "semantic_review":{"is_verified":True,"reviewer":"Codex","reason":"Ứng viên đúng nguồn",
                               "candidate_grade":"pass","source_hash":h,"candidate_hash":h}}
    result = evaluate_paired_dossier([case], [answer], [answer])
    assert result.get("gates", {}).get("targeted_score_improved") is not True
    assert result.get("gates", {}).get("promoted") is not True


def test_registry_rejects_arbitrary_nonempty_evidence(tmp_path):
    from app.active_registry import ActiveAdapterRegistry
    import pytest
    registry = ActiveAdapterRegistry(tmp_path / "active.json")
    adapter = tmp_path / "candidate"
    adapter.mkdir()
    (adapter / "adapters.safetensors").write_bytes(b"isolated-unreviewed-weights")
    with pytest.raises(ValueError):
        registry.promote_adapter("fake-evidence", adapter, {
            "semantically_accepted": True, "reviewed_by_codex": True,
            "evidence": "this string is not a bound reviewed dossier",
        })
    assert registry.get_active_adapter_dir() is None


def test_registry_readback_rejects_unbound_stored_flag(tmp_path):
    from app.active_registry import ActiveAdapterRegistry
    registry = ActiveAdapterRegistry(tmp_path / "active.json")
    adapter = tmp_path / "candidate"
    adapter.mkdir()
    (adapter / "adapters.safetensors").write_bytes(b"unchecked")
    registry.save_registry({"active_adapter_id": "unchecked", "adapter_dir": str(adapter),
                            "accepted_adapters": {"unchecked": {"semantically_accepted": True}}})
    assert registry.get_active_adapter_dir() is None


def test_paired_improvement_requires_frozen_protocol_and_full_base_review():
    import hashlib
    from app.paired_evaluation import evaluate_paired_dossier
    source, base, candidate = "Independent source.", "Wrong", "Correct [S1]"
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()
    cases = [{"id": "target", "category": "targeted_repair", "passage": source,
              "semantic_review": {"is_verified": True, "reviewer": "Codex", "reason": "checked",
                                  "source_hash": h(source), "base_hash": h(base),
                                  "candidate_hash": h(candidate), "base_grade": "fail",
                                  "candidate_grade": "pass"}}]
    result = evaluate_paired_dossier(cases, [base], [candidate])
    assert result.get("gates", {}).get("promoted") is not True, (
        "one reviewed target without frozen coverage/thresholds cannot certify promotion")


def test_trial_signature_binds_weights_content_not_only_size(tmp_path):
    from app.run_ledger import compute_signature_hash
    (tmp_path / "config.json").write_text('{}')
    (tmp_path / "tokenizer.json").write_text('{}')
    weights = tmp_path / "model.safetensors"
    weights.write_bytes(b"base-version-one")
    args = dict(config={"iterations": 1}, base_model_dir=tmp_path,
                dataset_sha256="dataset", target_hypothesis="preserve exact base",
                frozen_holdout_id="frozen", code_fingerprint={"runner": "fixed"})
    before = compute_signature_hash(**args)
    weights.write_bytes(b"base-version-two")
    assert compute_signature_hash(**args) != before


def test_trial_signature_binds_middle_of_large_weights(tmp_path):
    from app.run_ledger import compute_signature_hash
    (tmp_path / "config.json").write_text('{}')
    (tmp_path / "tokenizer.json").write_text('{}')
    weights = tmp_path / "model.safetensors"
    with weights.open("wb") as f:
        f.truncate(17 * 1024 * 1024)
    args = dict(config={"iterations": 1}, base_model_dir=tmp_path,
                dataset_sha256="dataset", target_hypothesis="preserve exact base",
                frozen_holdout_id="frozen", code_fingerprint={"runner": "fixed"})
    before = compute_signature_hash(**args)
    with weights.open("r+b") as f:
        f.seek(8 * 1024 * 1024)
        f.write(b"changed-middle")
    assert compute_signature_hash(**args) != before


def test_bound_trial_manifest_cannot_be_rebound(tmp_path):
    from app.run_ledger import RunLedger
    import pytest
    ledger = RunLedger(tmp_path / "runs", tmp_path / "index.jsonl")
    args = dict(config={"iterations": 1}, base_model_dir=tmp_path,
                dataset_dir=tmp_path, target_hypothesis="retain immutable evidence",
                baseline_metrics={"score": 0.5}, frozen_holdout_id="frozen")
    run = ledger.create_run(**args)
    ledger.bind_verified_manifest(run["run_id"], dataset_sha256="verified-original", **args)
    with pytest.raises(ValueError):
        ledger.bind_verified_manifest(run["run_id"], dataset_sha256="changed", **args)
    assert ledger.get_run(run["run_id"])["manifest"]["dataset"]["dataset_sha256"] == "verified-original"


def _ocr_training_fixture(tmp_path, monkeypatch, scanned, verified_page):
    import sqlite3
    from app.indexer import KnowledgeIndexer
    from app import training_data
    from app import config
    monkeypatch.setattr(config, "SRC_DIR", tmp_path)
    monkeypatch.setattr(training_data, "SRC_DIR", tmp_path, raising=False)
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(vision_ocr, "CACHE_DIR", cache)
    db_path = tmp_path / "knowledge.db"
    KnowledgeIndexer(db_path, tmp_path)
    import pymupdf
    doc = pymupdf.open()
    for _ in range(4):
        doc.new_page()
    source = tmp_path / "scanned.pdf"
    doc.save(source)
    doc.close()
    import hashlib
    file_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    (cache / ("a" * 64 + ".json")).write_text(json.dumps({
        "cache_key": "a" * 64, "source_hash": file_hash,
        "source_relpath": "scanned.pdf", "page_num": 1,
        "backend": "ollama_vision", "text": "Only page one was reviewed",
        "is_verified": verified_page, "verified_by": "fixture" if verified_page else None,
        "verified_at": "2026-10-03" if verified_page else None,
    }))
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO documents(filename,clean_title,filepath,file_size,file_hash,total_pages,extracted_pages_count,is_scanned,status) VALUES(?,?,?,?,?,?,?,?,?)",
                     ("scanned.pdf", "source", str(source), 100, file_hash, 4, 4, scanned, "indexed"))
        for page in range(1, 5):
            conn.execute("INSERT INTO chunks(doc_id,book_title,filename,page_num,chunk_index,text) VALUES(1,?,?,?,?,?)",
                         ("source", "scanned.pdf", page, page-1, "Unchecked OCR words. " * 30))
    monkeypatch.setattr(training_data, "is_substantive_excerpt", lambda text: True)
    return training_data, db_path


def test_reviewing_one_page_does_not_authorize_other_ocr_pages(tmp_path, monkeypatch):
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=1, verified_page=True)
    assert list(training_data.select_pairs(db_path)) == [], (
        "page 1 approval cannot release unchecked pages 2 and 3 into training")


def test_ocr_text_cannot_bypass_training_gate_via_document_scanned_flag(tmp_path, monkeypatch):
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=0, verified_page=False)
    assert list(training_data.select_pairs(db_path)) == [], (
        "OCR success changes indexing state, not verification of the selected page text")


def test_verified_ocr_must_bind_the_selected_chunk_text(tmp_path, monkeypatch):
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=1, verified_page=True)
    cache = tmp_path / "cache"
    original = json.loads((cache / ("a" * 64 + ".json")).read_text())
    for page in (2, 3):
        record = dict(original, page_num=page, text="Different text was reviewed.")
        (cache / (str(page) * 64 + ".json")).write_text(json.dumps(record))
    assert list(training_data.select_pairs(db_path)) == [], (
        "a verified page cannot release stale or different text into the dataset")


def test_ocr_common_prefix_does_not_authorize_unreviewed_tail(tmp_path, monkeypatch):
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=1, verified_page=True)
    cache = tmp_path / "cache"
    original = json.loads((cache / ("a" * 64 + ".json")).read_text())
    for page in (2, 3):
        record = dict(original, page_num=page, text=("Unchecked OCR words. " * 4) + "Reviewed ending.")
        (cache / (str(page) * 64 + ".json")).write_text(json.dumps(record))
    assert list(training_data.select_pairs(db_path)) == [], (
        "matching first 60 characters does not prove the rest of the selected chunk was reviewed")


def test_missing_source_file_cannot_authorize_native_training(tmp_path, monkeypatch):
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=0, verified_page=False)
    (tmp_path / "scanned.pdf").unlink()
    for p in (tmp_path / "cache").glob("*.json"):
        p.unlink()
    assert list(training_data.select_pairs(db_path)) == [], (
        "missing originals cannot become eligible native data through a synthetic-fixture exception")


def test_native_training_chunk_must_belong_to_actual_page(tmp_path, monkeypatch):
    import hashlib
    import sqlite3
    import pymupdf
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=0, verified_page=False)
    source = tmp_path / "scanned.pdf"; source.unlink()
    pdf = pymupdf.open()
    for _ in range(4):
        page = pdf.new_page()
        page.insert_textbox((30, 30, 550, 780),
                            "This real native page contains different information about independent vectors. " * 6)
    pdf.save(source); pdf.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE documents SET file_hash=?", (digest,))
    for p in (tmp_path / "cache").glob("*.json"):
        p.unlink()
    assert list(training_data.select_pairs(db_path)) == [], (
        "having any native text on a page does not bind a different database chunk to that page")


def test_missing_ocr_cache_does_not_turn_scanned_page_into_native(tmp_path, monkeypatch):
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=0, verified_page=False)
    for p in (tmp_path / "cache").glob("*.json"):
        p.unlink()
    assert list(training_data.select_pairs(db_path)) == [], (
        "native classification must have actual page provenance when a PDF page is image-only")


def test_mixed_pdf_native_pages_remain_eligible_with_ocr_elsewhere(tmp_path, monkeypatch):
    import hashlib
    import sqlite3
    import pymupdf
    training_data, db_path = _ocr_training_fixture(tmp_path, monkeypatch, scanned=0, verified_page=True)
    source = tmp_path / "scanned.pdf"
    source.unlink()
    pdf = pymupdf.open()
    passage = ("Native page passage about linear algebra and independent vectors. " * 8).strip()
    for page_num in range(1, 5):
        page = pdf.new_page()
        if page_num != 1:
            page.insert_textbox((30, 30, 550, 780), passage, fontsize=11)
    pdf.save(source)
    pdf.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    cp = tmp_path / "cache" / ("a" * 64 + ".json")
    record = json.loads(cp.read_text()); record["source_hash"] = digest
    cp.write_text(json.dumps(record))
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE documents SET file_hash=?", (digest,))
        conn.execute("UPDATE chunks SET text=? WHERE page_num>1", (passage,))
    assert len(list(training_data.select_pairs(db_path))) == 1, (
        "a reviewed OCR page cannot prevent genuine native passages on other pages from being used")


def test_registry_rejects_existing_json_without_actual_paired_evidence(tmp_path, monkeypatch):
    from app import active_registry as registry_module
    import pytest
    registry = registry_module.ActiveAdapterRegistry(tmp_path / "active.json")
    adapter = tmp_path / "candidate"
    adapter.mkdir()
    (adapter / "adapters.safetensors").write_bytes(b"isolated-unreviewed-weights")
    evidence = tmp_path / "empty-evidence.json"
    base = tmp_path / "base"
    base.mkdir()
    (base / "model.safetensors").write_bytes(b"isolated-base-weights")
    monkeypatch.setattr(registry_module, "MLX_MODEL_DIR", base)
    for payload in ({}, {"unrelated": True}, {"reviewed_by_codex": True, "gates": {"promoted": True}},
                    {"cases": [{"unrelated": True}], "gates": {"promoted": True}},
                    {"raw_inputs": ["not evaluated inputs"], "case_records": [True]},
                    {"cases": [{"id": "fake", "question": "not a frozen input",
                                "base_answer": "not an actual reviewed output"}],
                     "gates": {"promoted": True}},
                    {"cases": [{"id": "fake", "question": "not a frozen input",
                                "passage": "unchecked source", "base_answer": "unchecked base",
                                "candidate_answer": "unchecked candidate",
                                "semantic_review": {"is_verified": True, "reviewer": "Codex",
                                                    "base_grade": "fail", "candidate_grade": "pass",
                                                    "reason": "unbound assertion"}}],
                     "gates": {"promoted": True}}):
        evidence.write_text(json.dumps(payload))
        with pytest.raises(ValueError):
            registry.promote_adapter("unreviewed-evidence", adapter, {
                "semantically_accepted": True, "reviewed_by_codex": True,
                "evidence_path": str(evidence),
            })
    assert registry.get_active_adapter_dir() is None


def test_registry_resolve_requires_actual_evidence_not_hash_string(tmp_path):
    import hashlib
    from app.active_registry import ActiveAdapterRegistry
    registry = ActiveAdapterRegistry(tmp_path / "active.json")
    adapter = tmp_path / "candidate"
    adapter.mkdir()
    content = b"unchecked-weights"
    (adapter / "adapters.safetensors").write_bytes(content)
    registry.save_registry({"active_adapter_id": "unchecked", "adapter_dir": str(adapter),
                           "accepted_adapters": {"unchecked": {
                               "semantically_accepted": True,
                               "adapter_sha256": hashlib.sha256(content).hexdigest(),
                               "protocol_sha256": "a" * 64}}})
    assert registry.get_active_adapter_dir() is None


def test_paired_case_ids_do_not_authorize_changed_frozen_inputs():
    import hashlib
    from copy import deepcopy
    from app.paired_evaluation import evaluate_paired_dossier
    protocol = {"schema": "independent-frozen-probe", "frozen_at": "2026-10-03T00:00:00Z",
                "decoding": {"temperature": 0, "max_tokens": 256, "seed": 0},
                "acceptance": {"min_target_accuracy": 0.8, "min_absolute_gain": 0.05,
                               "max_retention_regressions": 0, "max_critical_regressions": 0,
                               "claim_review_required": True, "no_source_all_pass": True},
                "cases": [{"id": "target", "kind": "target", "question": "Frozen question",
                           "passage": "Frozen source", "critical": True},
                          {"id": "retention", "kind": "retention", "question": "Retain",
                           "passage": "Retention source"},
                          {"id": "no-source", "kind": "retention", "question": "Unknown",
                           "passage": "", "is_no_source": True}]}
    cases = deepcopy(protocol["cases"])
    cases[0]["passage"] = "A different easier source"
    bases, candidates = ["Wrong", "Correct", "Refusal"], ["Correct", "Correct", "Refusal"]
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()
    for i, case in enumerate(cases):
        case["semantic_review"] = {"is_verified": True, "reviewer": "Codex", "reason": "checked",
                                   "source_hash": h(case["passage"]), "base_hash": h(bases[i]),
                                   "candidate_hash": h(candidates[i]),
                                   "base_grade": "fail" if i == 0 else "pass", "candidate_grade": "pass"}
    result = evaluate_paired_dossier(cases, bases, candidates, protocol=protocol)
    assert result.get("gates", {}).get("promoted") is not True, (
        "matching IDs do not certify passage/question/messages matching the frozen protocol")


def test_invalid_legacy_adapter_does_not_disable_shared_base(tmp_path, monkeypatch):
    from app import trained_client
    base = tmp_path / "base"
    base.mkdir()
    (base / "config.json").write_text('{}')
    (base / "model.safetensors").write_bytes(b"isolated-readiness-fixture")
    (base / "tokenizer.json").write_text('{}')
    (base / "tokenizer_config.json").write_text('{}')
    runtime = tmp_path / ".train-venv" / "bin" / "python"
    runtime.parent.mkdir(parents=True)
    runtime.touch()
    runtime.chmod(0o755)
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "ready.json").write_text('{}')
    monkeypatch.setattr(trained_client, "MLX_MODEL_DIR", base)
    monkeypatch.setattr(trained_client, "BASE_DIR", tmp_path)
    monkeypatch.setattr(trained_client, "MLX_ADAPTER_DIR", legacy)
    monkeypatch.setattr(trained_client, "active_registry", SimpleNamespace(get_active_adapter_dir=lambda: None))
    assert trained_client.TrainedModelClient.available() is True


def test_shared_base_readiness_requires_weights_tokenizer_and_runtime(tmp_path, monkeypatch):
    from app import trained_client
    base = tmp_path / "base"; base.mkdir()
    (base / "config.json").write_text('{}')
    (base / "model.safetensors").write_bytes(b"isolated-base")
    (base / "tokenizer.json").write_text('{}')
    (base / "tokenizer_config.json").write_text('{}')
    runtime = tmp_path / ".train-venv/bin/python"; runtime.parent.mkdir(parents=True)
    runtime.touch(); runtime.chmod(0o755)
    monkeypatch.setattr(trained_client, "MLX_MODEL_DIR", base)
    monkeypatch.setattr(trained_client, "BASE_DIR", tmp_path)
    monkeypatch.setattr(trained_client, "active_registry", SimpleNamespace(get_active_adapter_dir=lambda: None))
    for p in (base / "model.safetensors", base / "tokenizer.json", runtime):
        data = p.read_bytes(); p.unlink()
        assert trained_client.TrainedModelClient.available() is False, p.name
        p.write_bytes(data)
        if p == runtime:
            p.chmod(0o755)


def test_shared_text_completion_forwards_actual_decoding_parameters(monkeypatch):
    from app import trained_client
    monkeypatch.setattr(trained_client.TrainedModelClient, "available", classmethod(lambda cls: True))
    monkeypatch.setattr(trained_client, "active_registry", SimpleNamespace(get_active_adapter_dir=lambda: None))
    captured = []
    def infer(*args, **kwargs):
        captured.append(json.loads(kwargs["input"]))
        return SimpleNamespace(returncode=0, stdout=json.dumps({"answer": "fixture", "is_truncated": False}))
    monkeypatch.setattr(trained_client.subprocess, "run", infer)
    answer = trained_client.TrainedModelClient().chat_complete(
        [{"role": "user", "content": "probe"}], temperature=0, seed=12, max_tokens=33)
    assert answer == "fixture"
    assert captured[0]["temperature"] == 0 and captured[0]["seed"] == 12
    assert captured[0]["max_tokens"] == 33 and captured[0]["adapter_path"] is None


def _complete_paired_probe():
    import hashlib
    from copy import deepcopy
    protocol = {"schema": "independent-frozen-probe", "frozen_at": "2026-10-03T00:00:00Z",
                "decoding": {"temperature": 0, "max_tokens": 256, "seed": 0},
                "acceptance": {"min_target_accuracy": 0.8, "min_absolute_gain": 0.05,
                               "max_retention_regressions": 0, "max_critical_regressions": 0,
                               "claim_review_required": True, "no_source_all_pass": True},
                "cases": [{"id": "target", "kind": "target", "question": "Frozen question",
                           "passage": "Frozen source", "critical": True,
                           "messages": [{"role": "user", "content": "Frozen prompt"}],
                           "source_hash": "a" * 64},
                          {"id": "retention", "kind": "retention", "question": "Retain",
                           "passage": "Retention source"},
                          {"id": "no-source", "kind": "retention", "question": "Unknown",
                           "passage": "", "is_no_source": True}]}
    cases = deepcopy(protocol["cases"])
    bases, candidates = ["Wrong", "Correct", "Refusal"], ["Correct", "Correct", "Refusal"]
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()
    for i, case in enumerate(cases):
        case["semantic_review"] = {"is_verified": True, "reviewer": "Codex", "reason": "checked",
                                   "base_reason": "checked baseline", "candidate_reason": "checked candidate",
                                   "source_hash": h(case["passage"]), "base_hash": h(bases[i]),
                                   "candidate_hash": h(candidates[i]),
                                   "base_grade": "fail" if i == 0 else "pass", "candidate_grade": "pass"}
    return protocol, cases, bases, candidates


def test_paired_protocol_cannot_lose_required_frozen_fields():
    from copy import deepcopy
    from app.paired_evaluation import evaluate_paired_dossier
    protocol, originals, bases, candidates = _complete_paired_probe()
    for key in ("question", "messages", "source_hash", "critical"):
        cases = deepcopy(originals)
        cases[0].pop(key)
        result = evaluate_paired_dossier(cases, bases, candidates, protocol=protocol)
        assert result.get("gates", {}).get("promoted") is not True, key


def test_paired_retention_requires_baseline_hash_and_explicit_grade():
    from copy import deepcopy
    from app.paired_evaluation import evaluate_paired_dossier
    protocol, originals, bases, candidates = _complete_paired_probe()
    for key in ("base_hash", "base_grade"):
        cases = deepcopy(originals)
        cases[1]["semantic_review"].pop(key)
        result = evaluate_paired_dossier(cases, bases, candidates, protocol=protocol)
        assert result.get("gates", {}).get("promoted") is not True, key


def test_paired_no_source_and_case_kind_are_frozen():
    from copy import deepcopy
    from app.paired_evaluation import evaluate_paired_dossier
    protocol, originals, bases, candidates = _complete_paired_probe()
    for field, value in (("is_no_source", False), ("kind", "target")):
        cases = deepcopy(originals)
        cases[2][field] = value
        result = evaluate_paired_dossier(cases, bases, candidates, protocol=protocol)
        assert result.get("gates", {}).get("promoted") is not True, field


def test_cli_training_preserves_model_and_learning_rate_contract(monkeypatch, tmp_path):
    import run
    from app import fine_tune
    captured = []
    def train_request(data_dir, iterations=80, num_layers=4, adapter_dir=None,
                      model_dir=None, learning_rate=0.00002, max_seq_length=1024, **kwargs):
        captured.append((model_dir, learning_rate, max_seq_length))
    monkeypatch.setattr(fine_tune, "train", train_request)
    run.cmd_train(SimpleNamespace(data=tmp_path / "dataset", iters=80, num_layers=4,
                                 adapter_dir=tmp_path / "adapter", model_dir=None,
                                 learning_rate=0.00002, max_seq_length=1024))
    model, lr, seq = captured[0]
    assert model is None or isinstance(model, Path), "learning rate cannot become model path"
    assert lr == 0.00002 and seq == 1024


def _ocr_api_pdf(tmp_path, monkeypatch):
    import pymupdf
    from app import server
    p = tmp_path / "api-source.pdf"
    doc = pymupdf.open(); doc.new_page(); doc.save(p); doc.close()
    monkeypatch.setattr(server.document_lookup, "file_path", lambda name: p)
    return server


def test_ocr_invalid_page_preserves_client_error_status(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    server = _ocr_api_pdf(tmp_path, monkeypatch)
    with TestClient(server.app) as client:
        response = client.post("/api/ocr/run-page", json={"filename": "api-source.pdf", "page_num": 2})
    assert response.status_code == 400, response.text


def test_blocking_ocr_backend_does_not_run_on_web_event_loop(tmp_path, monkeypatch):
    import asyncio
    import threading
    server = _ocr_api_pdf(tmp_path, monkeypatch)
    worker_threads = []
    def backend(self, **kwargs):
        worker_threads.append(threading.get_ident())
        return {"text": "isolated OCR fixture", "needs_review": True}
    monkeypatch.setattr(vision_ocr.VisionOCRManager, "ocr_image_bytes", backend)
    loop_thread = threading.get_ident()
    asyncio.run(server.run_ocr_page(server.OCRRunPageRequest(filename="api-source.pdf", page_num=1)))
    assert worker_threads and worker_threads[0] != loop_thread, (
        "OCR uses blocking rendering/backend calls; web health/chat controls must remain responsive")


def _registry_isolated_weights(tmp_path, monkeypatch):
    from app import active_registry as mod
    adapter = tmp_path / "candidate"; adapter.mkdir()
    (adapter / "adapters.safetensors").write_bytes(b"unreviewed-candidate")
    base = tmp_path / "base"; base.mkdir()
    (base / "model.safetensors").write_bytes(b"isolated-base")
    monkeypatch.setattr(mod, "MLX_MODEL_DIR", base)
    return mod.ActiveAdapterRegistry(tmp_path / "active.json"), adapter


def test_registry_rejects_28_flagged_records_without_bound_artifacts(tmp_path, monkeypatch):
    import hashlib
    import pytest
    registry, adapter = _registry_isolated_weights(tmp_path, monkeypatch)
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()
    records = []
    for i in range(28):
        records.append({"id": "unbound-" + str(i), "question": "Question", "passage": "Source",
                        "base_answer": "Before", "candidate_answer": "After",
                        "semantic_review": {"is_verified": True, "reviewer": "Codex", "reason": "Assertion",
                                            "base_grade": "fail", "candidate_grade": "pass",
                                            "source_hash": h("Source"), "base_hash": h("Before"),
                                            "candidate_hash": h("After")}})
    p = tmp_path / "unbound.json"
    p.write_text(json.dumps({"cases": records, "gates": {"promoted": True}}))
    with pytest.raises(ValueError):
        registry.promote_adapter("unbound", adapter, {"semantically_accepted": True,
                                 "reviewed_by_codex": True, "evidence_path": str(p)})


def test_registry_rejects_seven_bound_json_files_with_unrelated_raw_inputs(tmp_path, monkeypatch):
    import hashlib
    import pytest
    registry, adapter = _registry_isolated_weights(tmp_path, monkeypatch)
    before, after = {}, {}
    for i in range(28):
        cid = "unrelated-" + str(i)
        after[cid] = {"kind": "target" if i < 20 else "retention", "grade": "pass",
                      "reason": "Unbound assertion", "answer_sha256": "a" * 64, "source_verified": True}
        before[cid] = dict(after[cid], grade="fail" if i < 20 else "pass")
    payloads = {"suite": {"unrelated": True}, "protocol": {"unrelated": True},
                "baseline_raw": {"unrelated": True}, "candidate_raw": {"unrelated": True},
                "baseline_review": {"cases": before}, "candidate_review": {"cases": after},
                "decision": {"status": "accepted", "promoted": True}}
    bindings = {}
    for name, data in payloads.items():
        p = tmp_path / (name + ".json"); p.write_text(json.dumps(data))
        bindings[name] = {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    dossier = tmp_path / "dossier.json"
    dossier.write_text(json.dumps({"schema": "codex-study-acceptance-v1", "reviewer": "Codex",
                                  "reviewed_by_codex": True, "bindings": bindings}))
    with pytest.raises(ValueError):
        registry.promote_adapter("unrelated", adapter, {"semantically_accepted": True,
                                 "reviewed_by_codex": True, "evidence_path": str(dossier)})


def test_registry_hash_cache_detects_change_with_preserved_mtime(tmp_path):
    import os
    import hashlib
    from app.active_registry import get_file_sha256_cached
    p = tmp_path / "weights"; p.write_bytes(b"version-one")
    stat = p.stat(); before = get_file_sha256_cached(p)
    p.write_bytes(b"version-two")
    os.utime(p, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert get_file_sha256_cached(p) == hashlib.sha256(b"version-two").hexdigest()
    assert get_file_sha256_cached(p) != before
