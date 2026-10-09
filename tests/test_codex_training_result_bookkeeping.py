"""A quality rejection must retain execution evidence and prevent blind retries."""
import json

from app.run_ledger import RunLedger, STATUS_REJECTED


def completed_run(tmp_path):
    ledger = RunLedger(tmp_path / "runs", tmp_path / "events.jsonl")
    record = {
        "run_id": "run-bookkeeping",
        "created_at": "2026-10-03T19:36:42Z",
        "status": "COMPLETED",
        "signature_hash": "unchanged-data-model-code-config",
        "manifest": {"dataset": {"dataset_sha256": "reviewed-release"}},
        "telemetry": {
            "start_time": "2026-10-03T19:36:46Z",
            "end_time": "2026-10-03T19:51:09Z",
            "duration_seconds": 863.0,
            "return_code": 0,
            "peak_memory_mb": 1945.4,
            "step_losses": [{"step": 160, "loss": 0.848}],
        },
        "checkpoints": [{"step": 160, "weights_hash": "retained-final-weights"}],
        "decision": "TRIAL_SUCCESSFUL",
    }
    (ledger.runs_dir / "run-bookkeeping.json").write_text(json.dumps(record))
    return ledger, record


def test_quality_rejection_preserves_actual_execution_clock_and_evidence(tmp_path, monkeypatch):
    ledger, original = completed_run(tmp_path)
    monkeypatch.setattr("app.run_ledger.time.strftime", lambda *_: "2026-10-04T10:00:00Z")
    result = ledger.update_status(
        original["run_id"], STATUS_REJECTED,
        diagnosis="Paired source review shows lower answer fidelity.",
        decision="REJECTED_NOT_PROMOTED",
    )
    assert result["telemetry"] == original["telemetry"]
    assert result["manifest"] == original["manifest"]
    assert result["checkpoints"] == original["checkpoints"]
    assert result["status"] == "REJECTED"
    event = json.loads(ledger.index_file.read_text().splitlines()[-1])
    assert event["status"] == "REJECTED"
    assert event["timestamp"] == "2026-10-04T10:00:00Z"


def test_unchanged_quality_rejected_run_cannot_train_again_without_remediation(tmp_path):
    ledger, record = completed_run(tmp_path)
    record["status"] = "REJECTED"
    record["decision"] = "REJECTED_NOT_PROMOTED"
    (ledger.runs_dir / "run-bookkeeping.json").write_text(json.dumps(record))
    blocked, reason, prior = ledger.check_duplicate_signature(record["signature_hash"])
    assert blocked is True
    assert prior["run_id"] == record["run_id"]
    assert "REJECTED" in reason
    assert ledger.get_run(record["run_id"])["checkpoints"] == record["checkpoints"]
