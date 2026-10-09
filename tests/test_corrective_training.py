"""Control-flow fixtures only: no MLX, real model calls, or personal history."""

import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.fine_tune as fine_tune
from app.config import TRAINING_MODEL_REPO
from app.corrective_training import assess_paired_reviews, model_files, sha256_file, validate_corrective_trial
from app.preflight_7b import ARCH_7B, preflight_check_7b_training


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def contract(tmp_path, monkeypatch):
    data, model, adapter = tmp_path / "data", tmp_path / "base", tmp_path / "new-adapter"
    data.mkdir(); model.mkdir()
    src = tmp_path / "src"; src.mkdir()
    (src / "fixture.pdf").write_bytes(b"control fixture; never a real source")
    monkeypatch.setattr("app.corrective_training.SRC_DIR", src)
    for name, n in (("train", 2048), ("valid", 200)):
        rows = [{"messages": [{"role": "user", "content": f"{name}-{i}"},
                               {"role": "assistant", "content": "control-flow fixture"}]} for i in range(n)]
        (data / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    digest = hashlib.sha256((data / "train.jsonl").read_bytes() + (data / "valid.jsonl").read_bytes()).hexdigest()
    (data / "approved_manifest.jsonl").write_text('{"control_fixture": true}\n')
    manifest_hash = sha256_file(data / "approved_manifest.jsonl")
    write_json(model / "config.json", {**ARCH_7B, "model_type": "qwen2", "quantization": {"bits": 4}})
    (model / "tokenizer.json").write_text("{}"); (model / "tokenizer_config.json").write_text("{}")
    (model / "model.safetensors").write_bytes(b"fixture, never loaded")
    hashes = {n: sha256_file(model / n) for n in model_files(model)}
    config = {"iterations": 80, "num_layers": 4, "learning_rate": 0.00002, "max_seq_length": 1024,
              "batch_size": 1, "grad_checkpoint": True, "mask_prompt": True}
    suite = {"cases": [{"id": f"{kind}-{i}", "kind": kind, "source_group": f"eval-{i}",
                        "error_id": "modality" if kind == "target" else None}
                       for kind in ("target", "retention") for i in range(30)]}
    write_json(data / "suite.json", suite)
    suite_binding = {"path": "suite.json", "sha256": sha256_file(data / "suite.json")}
    reports = {
        "diagnosis": {"reviewed_by_codex": True, "errors": [{"id": "modality", "cause_layer": "model_behavior",
            "diagnosis_confirmed": True, "hypothesis": "preserve MAY", "reproduction": "isolated fixture"}]},
        "baseline": {"complete": True, "content_review_complete": True, "production_model": "qwen2.5:7b",
            "production_digest": "fixture", "mlx_base_files_sha256": hashes, "suite_sha256": suite_binding["sha256"]},
        "dataset_release": {"dataset_sha256": digest, "approved": True, "independent_review_complete": True,
            "approved_manifest_sha256": manifest_hash, "source_files_sha256": {"fixture.pdf": sha256_file(src / "fixture.pdf")},
            "source_hashes_verified": True, "calibration_passed": True, "target_binding_verified": True,
            "source_group_disjoint": True, "holdout_leaks": 0, "distinct_train": 2048, "valid": 200,
            "source_groups": 400, "train_source_groups": [f"train-{i}" for i in range(300)],
            "valid_source_groups": [f"valid-{i}" for i in range(100)], "holdout_source_groups": ["holdout"]},
        "token_audit": {"dataset_sha256": digest, "base_files_sha256": hashes, "token_audit_uses_exact_tokenizer": True,
            "acceptable": True, "max_seq_length": 1024},
        "evaluation_protocol": {"frozen_before_training": True, "source_group_disjoint": True,
            "suite": suite_binding, "target_error_ids": ["modality"], "target_cases": 30, "retention_cases": 30,
            "acceptance": {"min_target_accuracy": 0.8, "min_absolute_gain": 0.15, "max_retention_drop": 0,
                           "max_retention_regressions": 0, "max_critical_regressions": 0,
                           "claim_review_required": True}},
    }
    plan = {"schema": "corrective-7b-v1", "status": "approved_for_trial", "executor": "Antigravity",
            "antigravity_chat_id": "fixture-new-chat", "model_dir": str(model), "adapter_dir": str(adapter),
            "dataset_sha256": digest, "config": config, "checkpoint": None,
            "base": {"repo": TRAINING_MODEL_REPO, "revision": "a" * 40, "files_sha256": hashes},
            "target_error_ids": ["modality"], "hypothesis": "preserve qualified claims",
            "change_from_previous": "first reviewed 7B error-specific trial", "evidence": {}}
    approval = {"dataset_sha256": digest, "codex_trial_approved": True, "approved_manifest_sha256": manifest_hash}

    def bind():
        for name, report in reports.items():
            path = data / f"{name}.json"; write_json(path, report)
            plan["evidence"][name] = {"path": path.name, "sha256": sha256_file(path)}
        write_json(data / "trial_plan.json", plan)
        approval["corrective_trial_sha256"] = sha256_file(data / "trial_plan.json")
        write_json(data / "approval.json", approval)

    bind()
    return SimpleNamespace(data=data, model=model, adapter=adapter, config=config,
                           plan=plan, approval=approval, reports=reports, bind=bind)


def validate(c):
    return validate_corrective_trial(c.data, c.model, c.adapter, c.approval, c.config)


def test_complete_evidence_can_authorize_control_flow_only(contract):
    assert validate(contract)["target_error_ids"] == ["modality"]


@pytest.mark.parametrize("name,key,value", [
    ("dataset_release", "calibration_passed", False),
    ("dataset_release", "distinct_train", 72),
    ("dataset_release", "holdout_leaks", 1),
    ("token_audit", "token_audit_uses_exact_tokenizer", False),
    ("token_audit", "max_seq_length", 1536),
    ("baseline", "production_model", "qwen2.5:3b"),
    ("evaluation_protocol", "retention_cases", 0),
])
def test_unchanged_hard_gates_block_trial(contract, name, key, value):
    contract.reports[name][key] = value; contract.bind()
    with pytest.raises(ValueError): validate(contract)


def test_code_or_retrieval_error_cannot_be_authorized_as_training(contract):
    contract.reports["diagnosis"]["errors"][0]["cause_layer"] = "retrieval"
    contract.bind()
    with pytest.raises(ValueError, match="lỗi thuộc mô hình"): validate(contract)


def test_changed_base_or_evidence_requires_new_review(contract):
    (contract.model / "tokenizer.json").write_text("changed")
    with pytest.raises(ValueError, match="base/tokenizer đã đổi"): validate(contract)


def test_changed_plan_and_config_are_not_covered_by_old_approval(contract):
    contract.plan["hypothesis"] = "new hypothesis"
    write_json(contract.data / "trial_plan.json", contract.plan)
    with pytest.raises(ValueError, match="approval"): validate(contract)


def test_evaluation_source_cannot_leak_into_training(contract):
    contract.reports["dataset_release"]["train_source_groups"][0] = "eval-0"
    contract.bind()
    with pytest.raises(ValueError, match="nguồn đánh giá rò"): validate(contract)


def test_physical_source_change_invalidates_release(contract, tmp_path):
    (tmp_path / "src/fixture.pdf").write_bytes(b"changed physical source")
    with pytest.raises(ValueError, match="PDF nguồn đã đổi"): validate(contract)


def test_7b_preflight_rejects_unknown_memory_fp16_and_silent_truncation(contract, monkeypatch):
    monkeypatch.setattr("app.preflight_7b.get_mac_memory_info", lambda: {
        "total_gb": 16, "available_gb": 12, "measurement_error": None})
    assert preflight_check_7b_training(contract.model)["eligible_for_training"]
    assert not preflight_check_7b_training(contract.model, max_seq_length=1536)["eligible_for_training"]
    write_json(contract.model / "config.json", {**ARCH_7B, "model_type": "qwen2"})
    assert not preflight_check_7b_training(contract.model)["eligible_for_training"]
    monkeypatch.setattr("app.preflight_7b.get_mac_memory_info", lambda: {
        "total_gb": 16, "available_gb": None, "measurement_error": None})
    assert not preflight_check_7b_training(contract.model)["eligible_for_training"]


def test_interrupted_observer_stops_owned_child_before_releasing_lock(contract, tmp_path, monkeypatch):
    python = tmp_path / ".train-venv/bin/python"; python.parent.mkdir(parents=True); python.touch()
    monkeypatch.setattr(fine_tune, "BASE_DIR", tmp_path)
    monkeypatch.setattr("app.preflight_7b.preflight_check_7b_training", lambda **kwargs: {
        "eligible_for_training": True, "violations": []})
    stopped = []

    def interrupted_wait(timeout=None):
        if not stopped:
            raise RuntimeError("observer unavailable")
        stopped.append("reaped")
        return -15

    proc = SimpleNamespace(pid=123456, wait=interrupted_wait,
                           terminate=lambda: stopped.append("terminate"), kill=lambda: stopped.append("kill"))
    monkeypatch.setattr(fine_tune.subprocess, "Popen", lambda *args, **kwargs: proc)

    class Coordinator:
        @contextmanager
        def acquire_for_training(self, **kwargs):
            yield 0
            assert "reaped" in stopped, "release GPU ownership only after own child has stopped"

        def update_child_pid(self, pid):
            assert pid == proc.pid

    with pytest.raises(RuntimeError, match="observer unavailable"):
        fine_tune.train(contract.data, adapter_dir=contract.adapter, model_dir=contract.model,
                        coordinator=Coordinator(), evict_ollama=False)
    checkpoint = json.loads((contract.adapter / "orchestration_checkpoint.json").read_text())
    assert checkpoint["status"] == "interrupted_by_exception"
    assert checkpoint["return_code"] == -15
    assert stopped == ["terminate", "reaped"] and not (contract.adapter / "ready.json").exists()


def test_incomplete_current_corpus_blocks_training_before_gpu(contract, tmp_path, monkeypatch):
    monkeypatch.setattr(fine_tune, 'BASE_DIR', tmp_path)
    runtime = tmp_path/'data/runtime'; runtime.mkdir(parents=True)
    write_json(runtime/'corpus_completion_policy.json', {'require_complete_corpus': True})
    monkeypatch.setattr('app.preflight_7b.preflight_check_7b_training', lambda **kwargs: {
        'eligible_for_training': True, 'violations': []})
    monkeypatch.setattr(fine_tune.subprocess, 'Popen', lambda *a, **k: pytest.fail('GPU launch forbidden'))
    with pytest.raises(RuntimeError, match='CORPUS_INCOMPLETE'):
        fine_tune.train(contract.data, adapter_dir=contract.adapter, model_dir=contract.model)
    assert not contract.adapter.exists()


def test_legacy_approval_cannot_start_gpu_or_create_output(contract, monkeypatch):
    contract.approval.pop("corrective_trial_sha256")
    write_json(contract.data / "approval.json", contract.approval)
    monkeypatch.setattr(fine_tune.subprocess, "Popen", lambda *a, **k: pytest.fail("GPU launch forbidden"))
    with pytest.raises(ValueError, match="approval"):
        fine_tune.train(contract.data, adapter_dir=contract.adapter, model_dir=contract.model)
    assert not contract.adapter.exists()


def test_target_gain_cannot_hide_loss_of_previously_correct_answers(contract):
    suite = json.loads((contract.data / "suite.json").read_text())
    def review(improved):
        return {"content_review_complete": True, "reviewer": "Codex", "cases": {
            c["id"]: {"input_sha256": c["id"], "reason": "fixture claim review", "source_verified": True,
                      "grade": "pass" if improved or c["kind"] == "retention" else "fail"}
            for c in suite["cases"]}}
    before, after = review(False), review(True)
    criteria = contract.reports["evaluation_protocol"]["acceptance"]
    passed = assess_paired_reviews(suite, before, after, criteria)
    assert passed["status"] == "quality_gate_passed_pending_codex_decision" and passed["promoted"] is False
    after["cases"]["retention-0"]["grade"] = "partial"
    rejected = assess_paired_reviews(suite, before, after, criteria)
    assert rejected["status"] == "rejected_quality" and rejected["retention_regressions"] == ["retention-0"]
    before["content_review_complete"] = False
    with pytest.raises(ValueError, match="chưa chấm nội dung"):
        assess_paired_reviews(suite, before, after, criteria)


def test_codex_executor_requires_confirmed_takeover(contract):
    data, model, adapter, approval, plan, config = (contract.data, contract.model, contract.adapter, contract.approval, contract.plan, contract.config)
    plan['executor'] = 'Codex'
    write_json(data / 'trial_plan.json', plan)
    approval['corrective_trial_sha256'] = sha256_file(data / 'trial_plan.json')
    with pytest.raises(ValueError, match='tiếp quản'):
        validate_corrective_trial(data, model, adapter, approval, config)


def test_confirmed_codex_executor_can_run_authorized_trial(contract):
    data, model, adapter, approval, plan, config = (contract.data, contract.model, contract.adapter, contract.approval, contract.plan, contract.config)
    takeover = {'exclusive_writer':'Codex','antigravity_chat_id':plan['antigravity_chat_id'],
                'execution_cancelled':True,'queued_delta_removed':True,
                'reason':'Model unavailable; bounded fallback', 'confirmed_at':'2026-10-04T01:38:00+07:00'}
    write_json(data / 'takeover.json', takeover)
    plan['executor']='Codex'
    plan['executor_fallback']={'path':'takeover.json','sha256':sha256_file(data / 'takeover.json')}
    write_json(data / 'trial_plan.json', plan)
    approval['corrective_trial_sha256']=sha256_file(data / 'trial_plan.json')
    assert validate_corrective_trial(data, model, adapter, approval, config)['executor']=='Codex'


def test_live_monitor_records_system_ram_usage(contract, tmp_path, monkeypatch):
    """A real monitor callback must persist measured RAM, even if child has no weights."""
    import importlib
    from app.run_ledger import RunLedger
    python=tmp_path/'.train-venv/bin/python';python.parent.mkdir(parents=True);python.touch()
    ledger=RunLedger(runs_dir=tmp_path/'runs', index_file=tmp_path/'index.jsonl')
    class Monitor:
        def __init__(self, **kw):self.callback=kw['telemetry_callback']
        def start(self):self.callback(6.0,1000.0)
        def stop(self):return {'abort_triggered':False,'peak_swap_used_mb':1000.0}
    class Coordinator:
        @contextmanager
        def acquire_for_training(self, **kw):yield 0
        def update_child_pid(self, pid):pass
    try:
        with monkeypatch.context() as m:
            m.setattr('app.memory_preflight.get_hardware_memory_profile',lambda:{'total_gb':16.0})
            importlib.reload(fine_tune)
            m.setattr(fine_tune,'BASE_DIR',tmp_path)
            m.setattr(fine_tune,'LiveMemoryMonitor',Monitor)
            m.setattr('app.preflight_7b.preflight_check_7b_training',lambda **kw:{'eligible_for_training':True,'violations':[]})
            proc=SimpleNamespace(pid=123456,poll=lambda:0,wait=lambda **kw:0)
            m.setattr(fine_tune.subprocess,'Popen',lambda *a,**kw:proc)
            with pytest.raises(RuntimeError,match='không tìm thấy adapter'):
                fine_tune.train(contract.data,adapter_dir=contract.adapter,model_dir=contract.model,
                                coordinator=Coordinator(),evict_ollama=False,ledger=ledger)
        record=json.loads(next((tmp_path/'runs').glob('*.json')).read_text())
        assert record['telemetry']['system_memory_used_mb']==10240.0
    finally:
        importlib.reload(fine_tune)
