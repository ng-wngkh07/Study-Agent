import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import app.fine_tune as fine_tune


def test_new_dataset_version_requires_matching_approval(tmp_path):
    data_dir = tmp_path / "data" / "training" / "v2"
    data_dir.mkdir(parents=True)
    train = data_dir / "train.jsonl"
    valid = data_dir / "valid.jsonl"
    train.write_text("{}\n" * 20)
    valid.write_text("{}\n" * 2)
    with pytest.raises(ValueError, match="approval.json"):
        fine_tune.train(data_dir)
    (data_dir / "approval.json").write_text(json.dumps({"dataset_sha256": "stale"}))
    with pytest.raises(ValueError, match="thay đổi"):
        fine_tune.train(data_dir)


def test_training_trial_preserves_active_adapter(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "training" / "v1"
    data_dir.mkdir(parents=True)
    train_path = data_dir / "train.jsonl"
    valid_path = data_dir / "valid.jsonl"
    train_path.write_text("{}\n" * 20)
    valid_path.write_text("{}\n" * 2)
    digest = hashlib.sha256(train_path.read_bytes() + valid_path.read_bytes()).hexdigest()
    (data_dir / "approval.json").write_text(json.dumps({"dataset_sha256": digest}))

    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text(json.dumps({"hidden_size": 3584, "num_hidden_layers": 28}))
    training_python = tmp_path / ".train-venv" / "bin" / "python"
    training_python.parent.mkdir(parents=True)
    training_python.write_text("")
    active = tmp_path / "active"
    active.mkdir()
    (active / "ready.json").write_text("previous adapter")
    monkeypatch.setattr(fine_tune, "BASE_DIR", tmp_path)
    monkeypatch.setattr(fine_tune, "TRAINING_MODEL_DIR", model_dir)
    monkeypatch.setattr(fine_tune, "validate_corrective_trial", lambda *args: {"test_contract": True})
    monkeypatch.setattr("app.preflight_7b.preflight_check_7b_training", lambda **kwargs: {
        "eligible_for_training": True, "violations": []})

    def fake_popen(command, **_kwargs):
        adapter = Path(command[command.index("--adapter-path") + 1])
        (adapter / "adapters.safetensors").write_bytes(b"trial")
        assert command[command.index("--learning-rate") + 1] == "5e-05"
        assert command[command.index("--max-seq-length") + 1] == "1024"
        return SimpleNamespace(pid=99999, wait=lambda: 0, terminate=lambda: None, kill=lambda: None)

    test_coordinator = fine_tune.GPULockManager(
        lock_path=tmp_path / "data" / "runtime" / "gpu.lock",
        state_path=tmp_path / "data" / "runtime" / "gpu_state.json",
        intent_path=tmp_path / "data" / "runtime" / "gpu_intent.lock",
    )
    monkeypatch.setattr(fine_tune.subprocess, "Popen", fake_popen)
    from app.ollama_client import OllamaClient
    monkeypatch.setattr(OllamaClient, "unload_resident_models", lambda self, timeout=10.0: [])
    fine_tune.train(
        data_dir,
        iterations=40,
        adapter_dir=Path("trial"),
        learning_rate=0.00005,
        coordinator=test_coordinator,
        evict_ollama=False,
    )
    assert (active / "ready.json").read_text() == "previous adapter"
    assert json.loads((tmp_path / "trial" / "ready.json").read_text())["dataset_sha256"] == digest
    with pytest.raises(ValueError, match="đã chứa adapter"):
        fine_tune.train(data_dir, iterations=40, adapter_dir=active,
                       coordinator=test_coordinator, evict_ollama=False)
    assert (active / "ready.json").read_text() == "previous adapter"


def test_training_rejects_cross_book_data_entirely_removed_by_holdout(tmp_path):
    data_dir = tmp_path / "v1"
    data_dir.mkdir()
    train_file = data_dir / "train.jsonl"
    valid_file = data_dir / "valid.jsonl"
    train_file.write_text("{}\n" * 8)
    valid_file.write_text("{}\n" * 2)
    digest = hashlib.sha256(train_file.read_bytes() + valid_file.read_bytes()).hexdigest()
    (data_dir / "approval.json").write_text(json.dumps({"dataset_sha256": digest}))
    (data_dir / "summary.json").write_text(json.dumps({
        "cross_book_pairs": 7,
        "skipped_cross_book_pairs_for_holdout": 7,
    }))

    with pytest.raises(ValueError, match="Tất cả ví dụ liên sách đã bị loại"):
        fine_tune.train(data_dir)


def test_matching_chat_hash_cannot_authorize_incomplete_source_audit(tmp_path):
    data_dir = tmp_path / "v5"
    data_dir.mkdir()
    (data_dir/"train.jsonl").write_bytes(b"{}\n" * 20)
    (data_dir/"valid.jsonl").write_bytes(b"{}\n" * 2)
    digest = hashlib.sha256((data_dir/"train.jsonl").read_bytes() + (data_dir/"valid.jsonl").read_bytes()).hexdigest()
    (data_dir/"approval.json").write_text(json.dumps({"dataset_sha256": digest}))
    (data_dir/"summary.json").write_text(json.dumps({"audit_complete": False}))
    with pytest.raises(ValueError, match="Chưa kiểm tra xong"):
        fine_tune.train(data_dir)


def test_manifest_tampering_invalidates_training_approval(tmp_path):
    data_dir = tmp_path/"v5"
    data_dir.mkdir()
    (data_dir/"train.jsonl").write_bytes(b"{}\n" * 20)
    (data_dir/"valid.jsonl").write_bytes(b"{}\n" * 2)
    digest = hashlib.sha256((data_dir/"train.jsonl").read_bytes() + (data_dir/"valid.jsonl").read_bytes()).hexdigest()
    (data_dir/"approved_manifest.jsonl").write_text("modified sources")
    (data_dir/"approval.json").write_text(json.dumps({"dataset_sha256": digest, "approved_manifest_sha256": "previous"}))
    with pytest.raises(ValueError, match="Manifest"):
        fine_tune.train(data_dir)
