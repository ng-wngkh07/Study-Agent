"""Unit tests for 7B MLX training preflight checks, fail-closed measurements,
adapter metadata verification, and context truncation auditing.
"""

import json
from pathlib import Path
import pytest

from app.preflight_7b import (
    get_mac_memory_info,
    inspect_model_architecture,
    verify_model_adapter_compatibility,
    preflight_check_7b_training,
    audit_context_truncation,
    ARCH_7B,
    ARCH_3B
)


def test_mac_memory_info_structure():
    mem = get_mac_memory_info()
    assert "total_gb" in mem
    assert mem["total_gb"] is None or mem["total_gb"] >= 8.0
    assert "available_gb" in mem


def test_inspect_model_architecture(tmp_path):
    m7b_dir = tmp_path / "model_7b"
    m7b_dir.mkdir()
    (m7b_dir / "config.json").write_text(json.dumps({
        "hidden_size": ARCH_7B["hidden_size"],
        "num_hidden_layers": ARCH_7B["num_hidden_layers"],
        "vocab_size": 152064
    }))
    (m7b_dir / "model.safetensors").write_bytes(b"mock-weights")

    info7b = inspect_model_architecture(m7b_dir)
    assert info7b["model_type"] == "7B"
    assert info7b["has_weights"] is True

    m3b_dir = tmp_path / "model_3b"
    m3b_dir.mkdir()
    (m3b_dir / "config.json").write_text(json.dumps({
        "hidden_size": ARCH_3B["hidden_size"],
        "num_hidden_layers": ARCH_3B["num_hidden_layers"],
        "vocab_size": 151936
    }))

    info3b = inspect_model_architecture(m3b_dir)
    assert info3b["model_type"] == "3B"
    assert info3b["has_weights"] is False


def test_adapter_compatibility_fails_closed_without_metadata(tmp_path):
    """Missing adapter_config.json must fail closed (return False), not assume compatible."""
    m7b_dir = tmp_path / "model_7b"
    m7b_dir.mkdir()
    (m7b_dir / "config.json").write_text(json.dumps({
        "hidden_size": ARCH_7B["hidden_size"],
        "num_hidden_layers": ARCH_7B["num_hidden_layers"],
    }))

    empty_adapter_dir = tmp_path / "empty_adapter"
    empty_adapter_dir.mkdir()

    compatible, msg = verify_model_adapter_compatibility(m7b_dir, empty_adapter_dir)
    assert not compatible
    assert "Thiếu adapter_config.json" in msg


def test_adapter_compatibility_prevents_cross_architecture(tmp_path):
    m7b_dir = tmp_path / "model_7b"
    m7b_dir.mkdir()
    (m7b_dir / "config.json").write_text(json.dumps({
        "hidden_size": ARCH_7B["hidden_size"],
        "num_hidden_layers": ARCH_7B["num_hidden_layers"],
    }))

    adapter_3b_dir = tmp_path / "adapter_3b"
    adapter_3b_dir.mkdir()
    (adapter_3b_dir / "adapter_config.json").write_text(json.dumps({
        "base_model_name_or_path": "mlx-community/Qwen2.5-3B-Instruct-4bit"
    }))

    # Attempting to load 3B adapter onto 7B base model MUST be rejected
    compatible, msg = verify_model_adapter_compatibility(m7b_dir, adapter_3b_dir)
    assert not compatible
    assert "NGHIÊM CẤM" in msg
    assert "3B" in msg and "7B" in msg


def test_preflight_7b_training_rules(monkeypatch):
    # Mock sufficient RAM to isolate rule logic from OS state
    monkeypatch.setattr(
        "app.preflight_7b.get_mac_memory_info",
        lambda: {"total_gb": 16.0, "available_gb": 12.0, "free_gb": 6.0, "active_gb": 2.0, "inactive_gb": 6.0, "wired_gb": 2.0, "measurement_error": None}
    )
    # Pass with compliant params on 16GB Mac
    res_pass = preflight_check_7b_training(
        batch_size=1,
        num_layers=4,
        max_seq_length=1024,
        grad_checkpoint=True
    )
    assert res_pass["passed"]
    assert res_pass["estimated_peak_memory_gb"] <= 12.0
    assert not res_pass["is_empirical_measurement"]

    # Fail if batch_size > 1
    res_batch = preflight_check_7b_training(batch_size=2)
    assert not res_batch["passed"]
    assert any("Batch size" in v for v in res_batch["violations"])

    # Fail if grad_checkpoint is False
    res_grad = preflight_check_7b_training(grad_checkpoint=False)
    assert not res_grad["passed"]
    assert any("gradient checkpointing" in v for v in res_grad["violations"])

    # Fail if max_seq_length > 1024
    res_seq = preflight_check_7b_training(max_seq_length=2048)
    assert not res_seq["passed"]
    assert any("Độ dài chuỗi tối đa" in v for v in res_seq["violations"])


def test_adapter_without_weights_fails_closed(tmp_path):
    """Adapter with matching config but missing weights file must be rejected."""
    import struct
    hidden = ARCH_7B["hidden_size"]
    inter = ARCH_7B["intermediate_size"]
    layers = ARCH_7B["num_hidden_layers"]
    heads = 28
    kv_heads = 4

    m7b_dir = tmp_path / "model_7b"
    m7b_dir.mkdir()
    (m7b_dir / "config.json").write_text(json.dumps({
        "hidden_size": hidden,
        "intermediate_size": inter,
        "num_hidden_layers": layers,
        "num_attention_heads": heads,
        "num_key_value_heads": kv_heads,
        "head_dim": hidden // heads
    }))

    adapter_dir = tmp_path / "adapter_no_weights"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text(json.dumps({
        "base_model_name_or_path": "Qwen/Qwen2.5-7B-Instruct"
    }))

    compatible, msg = verify_model_adapter_compatibility(m7b_dir, adapter_dir)
    assert not compatible
    assert "Thiếu tệp trọng số LoRA" in msg

    # Even if file exists, if it's empty / dummy (< 1024 bytes) it must be rejected
    (adapter_dir / "adapters.safetensors").write_bytes(b"too small")
    compatible, msg = verify_model_adapter_compatibility(m7b_dir, adapter_dir)
    assert not compatible
    assert "quá nhỏ" in msg

    # Dummy file without valid safetensors layout must be rejected
    (adapter_dir / "adapters.safetensors").write_bytes(b"X" * 2048)
    compatible, msg = verify_model_adapter_compatibility(m7b_dir, adapter_dir)
    assert not compatible
    assert "không khớp" in msg or "không hợp lệ" in msg

    # Valid paired LoRA safetensors file must pass
    tensors = {
        "model.layers.1.self_attn.q_proj.lora_a": [hidden, 4],
        "model.layers.1.self_attn.q_proj.lora_b": [4, hidden],
    }
    header, payload = {}, bytearray()
    for name, shape in tensors.items():
        values = [0.05] * (shape[0] * shape[1])
        data = struct.pack("<" + "f" * len(values), *values)
        header[name] = {"dtype": "F32", "shape": shape, "data_offsets": [len(payload), len(payload) + len(data)]}
        payload.extend(data)
    encoded = json.dumps(header).encode()
    valid_safetensors = struct.pack("<Q", len(encoded)) + encoded + payload

    (adapter_dir / "adapters.safetensors").write_bytes(valid_safetensors)
    compatible, msg = verify_model_adapter_compatibility(m7b_dir, adapter_dir)
    assert compatible


def test_audit_context_truncation_with_valid_and_malformed(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    train_file = dataset_dir / "train.jsonl"
    valid_file = dataset_dir / "valid.jsonl"

    # Write samples within limit
    lines = []
    for i in range(10):
        lines.append(json.dumps({"messages": [{"role": "user", "content": "Ngắn"}, {"role": "assistant", "content": "Ngắn"}]}))
    train_file.write_text("\n".join(lines), encoding="utf-8")
    valid_file.write_text("\n".join(lines[:2]), encoding="utf-8")

    audit = audit_context_truncation(dataset_dir, max_seq_length=1024)
    assert audit["acceptable"] is True
    assert audit["train"]["malformed_samples"] == 0

    # Malformed record must fail closed
    malformed_dir = tmp_path / "malformed_dataset"
    malformed_dir.mkdir()
    (malformed_dir / "train.jsonl").write_text('{"messages": "not a list"}\n{"corrupt json\n', encoding="utf-8")
    (malformed_dir / "valid.jsonl").write_text("\n".join(lines[:2]), encoding="utf-8")

    malformed_audit = audit_context_truncation(malformed_dir, max_seq_length=1024)
    assert malformed_audit["acceptable"] is False
    assert malformed_audit["train"]["malformed_samples"] > 0

    # Missing valid.jsonl must fail closed
    missing_valid_dir = tmp_path / "missing_valid_dataset"
    missing_valid_dir.mkdir()
    (missing_valid_dir / "train.jsonl").write_text("\n".join(lines), encoding="utf-8")

    missing_audit = audit_context_truncation(missing_valid_dir, max_seq_length=1024)
    assert missing_audit["acceptable"] is False
