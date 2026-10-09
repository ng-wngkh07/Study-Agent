import json
from pathlib import Path
import struct

from app.adapter_integrity import inspect_mlx_adapter_layout


def fixtures(tmp_path: Path, wrong_dim=False, nonfinite=False):
    model = tmp_path / "model"
    model.mkdir()
    (model / "config.json").write_text(json.dumps({"hidden_size": 4, "intermediate_size": 8,
        "num_hidden_layers": 2, "num_attention_heads": 2, "num_key_value_heads": 1}))
    tensors = {
        "model.layers.1.self_attn.q_proj.lora_a": [3 if wrong_dim else 4, 2],
        "model.layers.1.self_attn.q_proj.lora_b": [2, 4],
    }
    header, payload = {}, bytearray()
    for name, shape in tensors.items():
        values = [float("nan") if nonfinite else 0.125] * (shape[0] * shape[1])
        data = struct.pack("<" + "f" * len(values), *values)
        header[name] = {"dtype": "F32", "shape": shape, "data_offsets": [len(payload), len(payload) + len(data)]}
        payload.extend(data)
    encoded = json.dumps(header).encode()
    file = tmp_path / "adapters.safetensors"
    file.write_bytes(struct.pack("<Q", len(encoded)) + encoded + payload)
    return model, file


def test_actual_paired_matrices_match_layout_but_not_base_identity(tmp_path):
    model, adapter = fixtures(tmp_path)
    result = inspect_mlx_adapter_layout(model, adapter)
    assert result["layout_matches"] and result["finite"]
    assert result["tensor_count"] == 2
    assert result["identity_verified"] is False


def test_wrong_matrix_dimensions_are_rejected(tmp_path):
    model, adapter = fixtures(tmp_path, wrong_dim=True)
    assert not inspect_mlx_adapter_layout(model, adapter)["layout_matches"]


def test_nonfinite_weights_are_rejected(tmp_path):
    model, adapter = fixtures(tmp_path, nonfinite=True)
    assert not inspect_mlx_adapter_layout(model, adapter)["layout_matches"]


def test_truncated_file_and_random_bytes_are_rejected(tmp_path):
    model, adapter = fixtures(tmp_path)
    adapter.write_bytes(adapter.read_bytes()[:-1])
    assert not inspect_mlx_adapter_layout(model, adapter)["layout_matches"]
    adapter.write_bytes(b"X" * 2048)
    assert not inspect_mlx_adapter_layout(model, adapter)["layout_matches"]


def test_invalid_json_header_type_and_nonexistent_module_are_rejected(tmp_path):
    model, adapter = fixtures(tmp_path)
    original = adapter.read_bytes()
    header_len = struct.unpack("<Q", original[:8])[0]
    header = json.loads(original[8:8 + header_len])
    bad_names = {k.replace("self_attn", "mlp"): v for k, v in header.items()}
    encoded = json.dumps(bad_names).encode()
    adapter.write_bytes(struct.pack("<Q", len(encoded)) + encoded + original[8 + header_len:])
    assert not inspect_mlx_adapter_layout(model, adapter)["layout_matches"]
    adapter.write_bytes(struct.pack("<Q", 2) + b"[]")
    assert not inspect_mlx_adapter_layout(model, adapter)["layout_matches"]
