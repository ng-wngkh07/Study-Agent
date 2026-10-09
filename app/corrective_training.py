"""Validate a reviewed, error-specific 7B trial before acquiring GPU resources.

These checks bind evidence, not semantic truth. Codex must independently review
the diagnoses, sources, calibration, and paired answers before issuing approval.
"""

import hashlib
import json
import re
from pathlib import Path

from app.config import SRC_DIR, TRAINING_MODEL_REPO


def sha256_file(path: Path) -> str:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError("Trial sửa lỗi 7B chưa đủ điều kiện: " + message)


def _evidence(data_dir: Path, binding: dict) -> dict:
    _require(isinstance(binding, dict), "thiếu hồ sơ bằng chứng")
    path = Path(binding.get("path", ""))
    path = path if path.is_absolute() else data_dir / path
    _require(path.is_file(), f"thiếu bằng chứng {path}")
    _require(sha256_file(path) == binding.get("sha256"), f"bằng chứng đã đổi: {path.name}")
    report = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(report, dict), f"bằng chứng không phải object: {path.name}")
    return report


def model_files(model_dir: Path) -> set[str]:
    names = {"config.json", "tokenizer.json", "tokenizer_config.json"}
    names.update(p.name for p in model_dir.glob("*.safetensors"))
    names.update(p.name for p in model_dir.glob("*.json") if p.name != "model_identity.json")
    names.update(p.name for p in model_dir.glob("*.txt"))
    return names


def validate_manual_content_review(manifest_records, review, dataset_digest, manifest_digest):
    """Manual source review binds each reference; it has no automatic judge to calibrate."""
    _require(review.get('reviewer') == 'Codex' and review.get('content_review_complete') is True and
             review.get('dataset_sha256') == dataset_digest and
             review.get('manifest_sha256') == manifest_digest, 'thiếu review nội dung đúng release')
    cases = review.get('cases', [])
    _require(len(cases) == len(manifest_records), 'review nội dung thiếu/thừa mẫu')
    by_id = {c.get('id'): c for c in cases}
    _require(len(by_id) == len(cases) and set(by_id) == {m['id'] for m in manifest_records},
             'review nội dung sai ID hoặc trùng mẫu')
    for m in manifest_records:
        c = by_id[m['id']]
        expected = {'source_file_sha256':m['source_file_sha256'],
                    'passage_sha256':sha256_text(m['passage']),
                    'query_sha256':sha256_text(m['query']),
                    'answer_sha256':sha256_text(m['reference'])}
        _require(c.get('grade') == 'pass' and c.get('source_verified') is True and c.get('reason') and
                 all(c.get(k) == v for k,v in expected.items()), 'review nội dung không khớp mẫu '+m['id'])


def sha256_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def validate_corrective_trial(data_dir: Path, model_dir: Path, adapter_dir: Path,
                              approval: dict, run_config: dict) -> dict:
    """Fail closed for old approvals, 3B targets, missing evidence, or changed inputs."""
    plan_path = data_dir / "trial_plan.json"
    _require(plan_path.is_file(), "cần trial_plan.json, không dùng lại approval của trial cũ")
    _require(approval.get("corrective_trial_sha256") == sha256_file(plan_path),
             "Codex approval chưa ràng buộc trial_plan.json")
    _require(approval.get("codex_trial_approved") is True, "chưa có quyết định Codex cho trial này")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    schema = plan.get("schema")
    _require(schema in ("corrective-7b-v1", "corrective-3b-v1") and plan.get("status") == "approved_for_trial",
             "hồ sơ đang draft hoặc sai protocol")
    executor = plan.get("executor")
    _require(executor in ("Antigravity", "Codex"), "bên thực thi chưa được xác nhận")
    if executor == "Codex":
        _require(isinstance(plan.get("executor_fallback"), dict), "thiếu bằng chứng tiếp quản")
        takeover = _evidence(data_dir, plan["executor_fallback"])
        _require(takeover.get("exclusive_writer") == "Codex" and
                 takeover.get("antigravity_chat_id") == plan.get("antigravity_chat_id") and
                 takeover.get("execution_cancelled") is True and
                 takeover.get("queued_delta_removed") is True and
                 takeover.get("reason") and takeover.get("confirmed_at"),
                 "chưa xác nhận tiếp quản độc quyền sau khi dừng tác vụ")
    _require(bool(plan.get("antigravity_chat_id")), "chưa ghi chat mới của trial")
    _require(Path(plan.get("model_dir", "")).resolve() == model_dir.resolve(), "sai đường dẫn base")
    _require(Path(plan.get("adapter_dir", "")).resolve() == adapter_dir.resolve(), "sai output mới")
    _require(plan.get("dataset_sha256") == approval.get("dataset_sha256"), "sai dataset binding")
    _require(plan.get("config") == run_config, "cấu hình thực thi khác cấu hình được duyệt")
    _require(plan.get("checkpoint") is None, "chưa hỗ trợ resume trong protocol này; không dùng adapter 3B")

    identity = plan.get("base", {})
    if schema == "corrective-3b-v1":
        _require(identity.get("repo") in (TRAINING_MODEL_REPO, "mlx-community/Qwen2.5-3B-Instruct-4bit"), "target phải là Qwen2.5 3B/7B Instruct 4-bit")
    else:
        _require(identity.get("repo") == TRAINING_MODEL_REPO, "target phải là Qwen2.5 7B Instruct 4-bit")
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", str(identity.get("revision", "")))), "base chưa pin revision")
    hashes = identity.get("files_sha256", {})
    _require(isinstance(hashes, dict) and set(hashes) == model_files(model_dir),
             "chưa ràng buộc toàn bộ config/tokenizer/trọng số base")
    _require(any(n.endswith(".safetensors") for n in hashes), "base thiếu trọng số thật")
    for name, digest in hashes.items():
        _require(Path(name).name == name and (model_dir / name).is_file(), "tệp base không hợp lệ")
        _require(sha256_file(model_dir / name) == digest, f"base/tokenizer đã đổi: {name}")

    evidence = plan.get("evidence", {})
    reports = {name: _evidence(data_dir, evidence.get(name)) for name in
               ("diagnosis", "baseline", "dataset_release", "token_audit", "evaluation_protocol")}
    diagnosis = reports["diagnosis"]
    _require(diagnosis.get("reviewed_by_codex") is True, "chẩn đoán chưa được rà soát")
    errors = diagnosis.get("errors", [])
    _require(bool(errors) and all(e.get("cause_layer") == "model_behavior" and
             e.get("diagnosis_confirmed") is True and e.get("hypothesis") and e.get("reproduction")
             for e in errors), "phải xác định lỗi thuộc mô hình và giả thuyết sửa; lỗi code/retrieval sửa riêng")
    error_ids = {e["id"] for e in errors}
    _require(set(plan.get("target_error_ids", [])) == error_ids, "sai nhóm lỗi được duyệt")

    baseline = reports["baseline"]
    _require(baseline.get("complete") is True and baseline.get("content_review_complete") is True,
             "baseline chưa sinh và chấm nội dung xong")
    if schema == "corrective-3b-v1":
        prod_model = baseline.get("production_model") or baseline.get("base_repo") or "qwen2.5-3b-4bit"
        prod_digest = baseline.get("production_digest") or baseline.get("base_revision")
        _require(prod_model in ("qwen2.5:3b", "qwen2.5-3b-4bit", "qwen2.5:7b", "mlx-community/Qwen2.5-3B-Instruct-4bit") and prod_digest,
                 "thiếu baseline bản 3B/7B đang dùng")
    else:
        _require(baseline.get("production_model") == "qwen2.5:7b" and baseline.get("production_digest"),
                 "thiếu baseline bản 7B đang dùng")
    b_hashes = baseline.get("mlx_base_files_sha256") or baseline.get("base_files_sha256")
    _require(b_hashes == hashes, "baseline MLX không cùng exact base")

    release = reports["dataset_release"]
    _require(release.get("dataset_sha256") == approval.get("dataset_sha256"), "release không cùng dữ liệu")
    manifest = data_dir / "approved_manifest.jsonl"
    _require(manifest.is_file() and approval.get("approved_manifest_sha256") == sha256_file(manifest) and
             release.get("approved_manifest_sha256") == approval.get("approved_manifest_sha256"),
             "manifest nguồn chưa ràng buộc với release/approval")
    source_hashes = release.get("source_files_sha256", {})
    _require(isinstance(source_hashes, dict) and source_hashes, "thiếu hash PDF nguồn thật")
    for name, digest in source_hashes.items():
        source_p = (SRC_DIR / name).resolve()
        _require(not Path(name).is_absolute() and source_p.is_file() and source_p.is_relative_to(SRC_DIR.resolve()),
                 f"tệp PDF nguồn không hợp lệ: {name}")
        _require(sha256_file(source_p) == digest, f"PDF nguồn đã đổi sau duyệt: {name}")
    for key in ("approved", "independent_review_complete", "source_hashes_verified",
                "target_binding_verified", "source_group_disjoint"):
        _require(release.get(key) is True, f"release gate chưa đạt: {key}")
    if release.get('review_method') == 'codex_manual_source_bound':
        _require(release.get('calibration_status') == 'not_applicable_no_automated_judge',
                 'chưa ghi rõ phương pháp duyệt thủ công')
        content = _evidence(data_dir, evidence.get('content_review'))
        manifest_records = [json.loads(s) for s in manifest.read_text().splitlines() if s.strip()]
        validate_manual_content_review(manifest_records, content, approval['dataset_sha256'],
                                       approval['approved_manifest_sha256'])
    else:
        _require(release.get('calibration_passed') is True, 'release gate chưa đạt: calibration_passed')
    _require(release.get("holdout_leaks") == 0, "rò rỉ holdout")
    if schema == "corrective-3b-v1" and plan.get("exploratory_trial") is True:
        min_train = release.get("min_distinct_train", 8)
        min_valid = release.get("min_valid", 2)
        min_groups = release.get("min_source_groups", 2)
        _require(isinstance(release.get("distinct_train"), int) and release["distinct_train"] >= min_train, f"gate distinct_train < {min_train}")
        _require(isinstance(release.get("valid"), int) and release["valid"] >= min_valid, f"gate valid < {min_valid}")
        _require(isinstance(release.get("source_groups"), int) and release["source_groups"] >= min_groups, f"gate source_groups < {min_groups}")
    else:
        for key, minimum in (("distinct_train", 2048), ("valid", 200), ("source_groups", 400)):
            _require(isinstance(release.get(key), int) and release[key] >= minimum, f"gate {key} < {minimum}")
    train_groups = set(release.get("train_source_groups", []))
    valid_groups = set(release.get("valid_source_groups", []))
    holdout_groups = set(release.get("holdout_source_groups", []))
    _require(len(train_groups | valid_groups) >= release["source_groups"] and valid_groups and holdout_groups,
             "thiếu danh sách nhóm nguồn để đối chiếu")
    _require(not train_groups & (valid_groups | holdout_groups) and not valid_groups & holdout_groups,
             "nhóm nguồn train/valid/holdout bị chồng lấn")
    partitions = []
    for name in ("train", "valid"):
        rows = [json.loads(s) for s in (data_dir / f"{name}.jsonl").read_text().splitlines() if s.strip()]
        _require(all(isinstance(r.get("messages"), list) and r["messages"] for r in rows), "mẫu sai schema")
        partitions.append({json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows})
    _require(len(partitions[0]) >= release["distinct_train"] and len(partitions[1]) >= release["valid"],
             "số mẫu duyệt không khớp dữ liệu thật hoặc mẫu trùng")
    _require(not partitions[0].intersection(partitions[1]), "trùng mẫu train/valid")

    token = reports["token_audit"]
    _require(token.get("dataset_sha256") == approval.get("dataset_sha256") and
             token.get("base_files_sha256") == hashes, "token audit không cùng dữ liệu/base")
    _require(token.get("token_audit_uses_exact_tokenizer") is True and token.get("acceptable") is True,
             "tokenizer chưa xác minh hoặc mẫu bị cắt")
    _require(token.get("max_seq_length") == run_config["max_seq_length"], "token audit sai context budget")

    protocol = reports["evaluation_protocol"]
    _require(protocol.get("frozen_before_training") is True and protocol.get("source_group_disjoint") is True,
             "bộ đánh giá chưa đóng băng/tách nguồn")
    _require(set(protocol.get("target_error_ids", [])) == error_ids, "bộ đánh giá sai nhóm lỗi")
    suite = _evidence(data_dir, protocol.get("suite"))
    _require(baseline.get("suite_sha256") == protocol["suite"]["sha256"], "baseline khác bộ đánh giá đóng băng")
    cases = suite.get("cases", [])
    _require(isinstance(cases, list) and all(isinstance(c, dict) and c.get("id") and c.get("source_group")
                                          for c in cases), "thiếu ca đánh giá/nhóm nguồn thật")
    _require(len({c["id"] for c in cases}) == len(cases), "ca đánh giá trùng ID")
    _require(not {c["source_group"] for c in cases} & train_groups, "nguồn đánh giá rò vào train")
    if schema == "corrective-3b-v1" and plan.get("exploratory_trial") is True:
        min_cases = 1
        for key in ("target_cases", "retention_cases"):
            _require(isinstance(protocol.get(key), int) and protocol[key] >= min_cases, f"thiếu {key}")
            kind = key.removesuffix("_cases")
            _require(sum(c.get("kind") == kind for c in cases) == protocol[key], "số ca báo cáo khác bộ đánh giá")
        err_map = protocol.get("target_error_mapping", {})
        covered = {c.get("error_id") or err_map.get(c.get("id")) for c in cases if c.get("kind") == "target"}
        _require(covered == error_ids, "ca đánh giá chưa phủ đúng lỗi")
        _require(all(sum(c.get("kind") == "target" and (c.get("error_id") or err_map.get(c.get("id"))) == error_id
                         for c in cases) >= 1 for error_id in error_ids), "thiếu ca cho lỗi mục tiêu")
    else:
        for key in ("target_cases", "retention_cases"):
            _require(isinstance(protocol.get(key), int) and protocol[key] >= 30, f"thiếu {key}")
            kind = key.removesuffix("_cases")
            _require(sum(c.get("kind") == kind for c in cases) == protocol[key], "số ca báo cáo khác bộ đánh giá")
        _require({c.get("error_id") for c in cases if c.get("kind") == "target"} == error_ids,
                 "ca đánh giá chưa phủ đúng lỗi")
        _require(all(sum(c.get("kind") == "target" and c.get("error_id") == error_id for c in cases) >= 30
                     for error_id in error_ids), "cần ít nhất 30 ca cho mỗi lỗi mục tiêu")
    criteria = protocol.get("acceptance", {})
    if schema == "corrective-3b-v1" and plan.get("exploratory_trial") is True:
        _require(criteria.get("min_target_accuracy", 0) >= 0.8 and
                 criteria.get("min_absolute_gain", 0) >= 0.05 and
                 criteria.get("max_retention_drop", 0) == 0 and
                 criteria.get("max_retention_regressions", 0) == 0 and
                 criteria.get("max_critical_regressions", 0) == 0 and
                 criteria.get("claim_review_required") is True, "chưa có tiêu chí cải thiện/giữ năng lực cũ đủ rõ")
    else:
        _require(criteria.get("min_target_accuracy", 0) >= 0.8 and
                 criteria.get("min_absolute_gain", 0) >= 0.15 and
                 criteria.get("max_retention_drop") == 0 and
                 criteria.get("max_retention_regressions") == 0 and
                 criteria.get("max_critical_regressions") == 0 and
                 criteria.get("claim_review_required") is True, "chưa có tiêu chí cải thiện/giữ năng lực cũ đủ rõ")
    _require(plan.get("hypothesis") and plan.get("change_from_previous"), "thiếu giả thuyết/thay đổi có căn cứ")
    return {"plan_sha256": sha256_file(plan_path), "base_files_sha256": hashes, "executor": executor,
            "target_error_ids": sorted(error_ids), "antigravity_chat_id": plan["antigravity_chat_id"]}


def assess_paired_reviews(suite: dict, baseline: dict, candidate: dict, criteria: dict) -> dict:
    """Measure a frozen, claim-reviewed comparison; never promote automatically."""
    for report in (baseline, candidate):
        _require(report.get("content_review_complete") is True and report.get("reviewer") == "Codex",
                 "chưa chấm nội dung độc lập; loss/judge/tests không thay thế review")
    expected = {c["id"] for c in suite["cases"]}
    _require(len(expected) == len(suite["cases"]), "trùng ca đánh giá")
    before, after = baseline["cases"], candidate["cases"]
    _require(set(before) == expected and set(after) == expected, "thiếu/thừa ca trong so sánh cặp")
    for case_id in expected:
        _require(before[case_id].get("input_sha256") == after[case_id].get("input_sha256") and
                 before[case_id].get("input_sha256"), "đầu vào trước/sau khác nhau")
        for report in (before, after):
            _require(report[case_id].get("grade") in {"pass", "partial", "fail"} and
                     report[case_id].get("reason") and report[case_id].get("source_verified") is True,
                     "thiếu grade/lý do/đối chiếu nguồn")
    failures, per_error = [], {}
    error_ids = {c["error_id"] for c in suite["cases"] if c["kind"] == "target"}
    for error_id in sorted(error_ids):
        ids = [c["id"] for c in suite["cases"] if c["kind"] == "target" and c["error_id"] == error_id]
        initial = sum(before[i]["grade"] == "pass" for i in ids) / len(ids)
        final = sum(after[i]["grade"] == "pass" for i in ids) / len(ids)
        per_error[error_id] = {"cases": len(ids), "before": initial, "after": final, "absolute_gain": final - initial}
        if final < criteria["min_target_accuracy"] or final - initial + 1e-12 < criteria["min_absolute_gain"]:
            failures.append("Lỗi chưa cải thiện đủ: " + error_id)
    retention = [c["id"] for c in suite["cases"] if c["kind"] == "retention"]
    _require(retention and error_ids, "thiếu nhóm lỗi hoặc nhóm giữ năng lực cũ")
    regressions = [i for i in retention if before[i]["grade"] == "pass" and after[i]["grade"] != "pass"]
    critical = [c["id"] for c in suite["cases"] if c.get("critical") is True and
                before[c["id"]]["grade"] == "pass" and after[c["id"]]["grade"] != "pass"]
    if len(regressions) > criteria["max_retention_regressions"]:
        failures.append("Mất câu trước đây trả lời đúng")
    if len(critical) > criteria["max_critical_regressions"]:
        failures.append("Hồi quy nghiêm trọng")
    return {"status": "rejected_quality" if failures else "quality_gate_passed_pending_codex_decision",
            "per_error": per_error, "retention_regressions": regressions,
            "critical_regressions": critical, "failures": failures, "promoted": False}
