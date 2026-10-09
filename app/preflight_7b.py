"""Hardware, memory, and model compatibility preflight checks for MLX 7B LoRA training.
Enforces strict 16GB Mac Unified Memory discipline, real tensor/metadata dimensions validation,
and fail-closed memory measurement without ungrounded defaults.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from app.config import BASE_DIR

logger = logging.getLogger(__name__)

# Constants for Qwen2.5 architectures
ARCH_7B = {"hidden_size": 3584, "num_hidden_layers": 28, "vocab_size": 152064, "intermediate_size": 18944}
ARCH_3B = {"hidden_size": 2048, "num_hidden_layers": 36, "vocab_size": 151936, "intermediate_size": 11008}


def get_mac_memory_info() -> Dict[str, Optional[float]]:
    """Retrieve total, wired, active, inactive, and free memory in gigabytes on macOS.

    FAIL-CLOSED: If sysctl or vm_stat fails, returns None for memory values rather than guessing.
    """
    total_bytes = None
    try:
        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, stderr=subprocess.DEVNULL).strip()
        total_bytes = int(out)
    except Exception as exc:
        logger.error("Failed to query sysctl hw.memsize: %s", exc)
        return {
            "total_gb": None,
            "free_gb": None,
            "inactive_gb": None,
            "active_gb": None,
            "wired_gb": None,
            "available_gb": None,
            "measurement_error": f"Không thể đọc sysctl hw.memsize: {exc}",
        }

    total_gb = total_bytes / (1024 ** 3)
    free_gb = None
    active_gb = None
    inactive_gb = None
    wired_gb = None

    try:
        vm_out = subprocess.check_output(["vm_stat"], text=True, stderr=subprocess.DEVNULL)
        page_size = 4096
        if "page size of" in vm_out:
            for line in vm_out.splitlines():
                if "page size of" in line:
                    parts = line.split("page size of")
                    if len(parts) > 1:
                        page_size = int(parts[1].split()[0])
                    break

        for line in vm_out.splitlines():
            line = line.strip()
            if line.startswith("Pages free:"):
                free_gb = (int(line.split(":")[1].strip().rstrip(".")) * page_size) / (1024 ** 3)
            elif line.startswith("Pages active:"):
                active_gb = (int(line.split(":")[1].strip().rstrip(".")) * page_size) / (1024 ** 3)
            elif line.startswith("Pages inactive:"):
                inactive_gb = (int(line.split(":")[1].strip().rstrip(".")) * page_size) / (1024 ** 3)
            elif line.startswith("Pages wired down:"):
                wired_gb = (int(line.split(":")[1].strip().rstrip(".")) * page_size) / (1024 ** 3)
    except Exception as exc:
        logger.error("Failed to parse vm_stat: %s", exc)
        return {
            "total_gb": round(total_gb, 2),
            "free_gb": None,
            "inactive_gb": None,
            "active_gb": None,
            "wired_gb": None,
            "available_gb": None,
            "measurement_error": f"Không thể đọc vm_stat: {exc}",
        }

    available_gb = (free_gb + inactive_gb) if (free_gb is not None and inactive_gb is not None) else None

    return {
        "total_gb": round(total_gb, 2),
        "free_gb": round(free_gb, 2) if free_gb is not None else None,
        "inactive_gb": round(inactive_gb, 2) if inactive_gb is not None else None,
        "active_gb": round(active_gb, 2) if active_gb is not None else None,
        "wired_gb": round(wired_gb, 2) if wired_gb is not None else None,
        "available_gb": round(available_gb, 2) if available_gb is not None else None,
        "measurement_error": None,
    }


def inspect_model_architecture(model_dir: Path) -> Dict[str, Any]:
    """Inspect model configuration in model_dir to determine parameter count and architecture."""
    config_file = model_dir / "config.json"
    if not config_file.exists():
        raise FileNotFoundError(f"config.json không tìm thấy trong {model_dir}")

    config = json.loads(config_file.read_text(encoding="utf-8"))
    hidden_size = config.get("hidden_size", 0)
    num_layers = config.get("num_hidden_layers", 0)

    is_7b = (hidden_size == ARCH_7B["hidden_size"] and num_layers == ARCH_7B["num_hidden_layers"])
    is_3b = (hidden_size == ARCH_3B["hidden_size"] and num_layers == ARCH_3B["num_hidden_layers"])

    model_type = "7B" if is_7b else ("3B" if is_3b else f"unknown_{hidden_size}_{num_layers}")

    # Check for weights existence
    has_safetensors = (model_dir / "model.safetensors").exists() or any(model_dir.glob("model-*.safetensors"))

    return {
        "model_dir": str(model_dir),
        "model_type": model_type,
        "hidden_size": hidden_size,
        "num_hidden_layers": num_layers,
        "intermediate_size": config.get("intermediate_size", 0),
        "vocab_size": config.get("vocab_size", 0),
        "has_weights": has_safetensors,
    }


def verify_model_adapter_compatibility(model_dir: Path, adapter_dir: Path) -> Tuple[bool, str]:
    """Strictly assert that adapter metadata and tensor dimensions match the target base model architecture.

    FAIL-CLOSED: If adapter_config.json is missing or lacks base model identity / dimensions,
    returns False. Does NOT assume compatibility.
    """
    if not adapter_dir.exists():
        return False, f"Thư mục adapter không tồn tại: {adapter_dir}"

    adapter_config_path = adapter_dir / "adapter_config.json"
    if not adapter_config_path.exists():
        return False, "Thiếu adapter_config.json: không thể xác minh danh tính và kiến trúc mô hình nền."

    try:
        model_info = inspect_model_architecture(model_dir)
        adapter_cfg = json.loads(adapter_config_path.read_text(encoding="utf-8"))

        base_identity = str(adapter_cfg.get("base_model_name_or_path", "")).strip()
        if not base_identity:
            return False, "adapter_config.json thiếu trường base_model_name_or_path: không xác định được mô hình nền."

        # Check dimension / architecture indicators in adapter config
        target_modules = adapter_cfg.get("target_modules", [])
        lora_dim = adapter_cfg.get("r", 0)

        # Cross-architecture mismatch check:
        # If adapter base name specifies 3B and target is 7B, or vice-versa
        is_adapter_3b = "3b" in base_identity.lower() or "3-b" in base_identity.lower()
        is_adapter_7b = "7b" in base_identity.lower() or "7-b" in base_identity.lower()

        if is_adapter_3b and model_info["model_type"] == "7B":
            return False, "NGHIÊM CẤM: Không thể áp dụng adapter 3B cho mô hình nền 7B (lệch số lớp 36 vs 28 và chiều ẩn 2048 vs 3584)."
        if is_adapter_7b and model_info["model_type"] == "3B":
            return False, "NGHIÊM CẤM: Không thể áp dụng adapter 7B cho mô hình nền 3B (lệch số lớp 28 vs 36 và chiều ẩn 3584 vs 2048)."

        # Require actual weights file (adapters.safetensors or weights.npz)
        safetensors_file = adapter_dir / "adapters.safetensors"
        npz_file = adapter_dir / "weights.npz"
        if not safetensors_file.exists() and not npz_file.exists():
            return False, "Thiếu tệp trọng số LoRA (không tìm thấy adapters.safetensors hoặc weights.npz trong thư mục adapter)."

        weights_file = safetensors_file if safetensors_file.exists() else npz_file
        if weights_file.stat().st_size < 1024:
            return False, f"Tệp trọng số {weights_file.name} quá nhỏ hoặc không chứa trọng số hợp lệ (< 1024 bytes)."

        # When safetensors file exists and model config is available, strictly inspect tensor shapes and finite values
        if safetensors_file.exists() and (model_dir / "config.json").exists():
            from app.adapter_integrity import inspect_mlx_adapter_layout
            layout_res = inspect_mlx_adapter_layout(model_dir, safetensors_file)
            if not layout_res.get("layout_matches"):
                return False, f"Cấu trúc trọng số adapter không khớp mô hình nền: {layout_res.get('error')}"
            if not layout_res.get("finite", True):
                return False, "Trọng số adapter chứa giá trị không hợp lệ (NaN hoặc Inf)."

        return True, f"Khớp kiến trúc {model_info['model_type']} với adapter cấu hình cho {base_identity}"
    except Exception as exc:
        return False, f"Lỗi kiểm tra tính tương thích adapter: {exc}"


def preflight_check_7b_training(
    model_dir: Optional[Path] = None,
    batch_size: int = 1,
    num_layers: int = 4,
    max_seq_length: int = 1024,
    grad_checkpoint: bool = True
) -> Dict[str, Any]:
    """Evaluate whether the local 16GB Apple Silicon Mac is eligible to train Qwen2.5 7B LoRA.

    Strict rules & Gating:
    - Fails closed if RAM measurement fails.
    - Physical RAM must be >= 15.5 GB.
    - Batch size must be exactly 1.
    - Gradient checkpointing must be enabled.
    - Max sequence length must not exceed 1024 tokens.
    - Number of LoRA layers must not exceed 8.
    - Estimated peak memory is gated against 12.0 GB ceiling.
    - Available RAM must meet minimum threshold.
    - Reports clear distinction: this is a pre-training estimation, NOT an actual empirical MLX peak measurement.
    """
    mem = get_mac_memory_info()
    violations = []

    # Rule 1: Fail closed if memory measurement failed
    if mem.get("measurement_error") or mem.get("total_gb") is None:
        violations.append(f"Không thể đo thông số RAM hệ thống ({mem.get('measurement_error')}); fail-closed không đủ điều kiện chạy 7B.")
        return {
            "passed": False,
            "eligible_for_training": False,
            "estimated_peak_memory_gb": None,
            "memory_info": mem,
            "violations": violations,
            "rationale": "Lỗi đo RAM hệ thống; fail-closed.",
        }

    total_gb = mem["total_gb"]
    available_gb = mem.get("available_gb")

    if total_gb < 15.5:
        violations.append(f"RAM vật lý ({total_gb} GB) không đạt mức tối thiểu 16 GB.")

    if batch_size != 1:
        violations.append(f"Batch size ({batch_size}) phải đúng bằng 1 cho mô hình 7B trên 16GB RAM.")

    if not grad_checkpoint:
        violations.append("Bắt buộc bật gradient checkpointing (--grad-checkpoint) cho mô hình 7B.")

    if max_seq_length < 1 or max_seq_length > 1024:
        violations.append(f"Độ dài chuỗi tối đa ({max_seq_length}) vượt quá 1024 tokens an toàn cho 16GB RAM.")

    if num_layers < 1 or num_layers > 8:
        violations.append(f"Số lớp LoRA ({num_layers}) quá lớn cho 16GB RAM (khuyến nghị 4-8 lớp).")

    # Estimated peak memory calculation (theoretical estimation):
    # 7B 4-bit weights ~ 4.45 GB
    # LoRA trainable params & AdamW state ~ 0.05 GB per layer
    # Activations with gradient checkpointing at seq 1024, batch 1 ~ 2.8 GB
    # System base & Python runtime ~ 1.5 GB
    estimated_peak_gb = 4.45 + (num_layers * 0.05) + (max_seq_length / 1024.0 * 2.8) + 1.5

    # Gating on estimated peak memory
    if estimated_peak_gb > 12.0:
        violations.append(f"Ước lượng peak memory ({estimated_peak_gb:.2f} GB) vượt trần an toàn 12.0 GB cho máy 16GB.")

    # Gating on available RAM (if measured)
    if available_gb is None:
        violations.append("Không đo được RAM khả dụng; không đủ điều kiện chạy 7B.")
    elif available_gb < estimated_peak_gb:
        violations.append(f"RAM khả dụng ({available_gb:.2f} GB) dưới ước lượng cần thiết ({estimated_peak_gb:.2f} GB); chờ tài nguyên đủ, không tự đóng job khác.")

    # Check model weights and disk space
    model_ready = False
    model_path_str = ""
    if model_dir:
        model_path_str = str(model_dir)
        if model_dir.exists():
            try:
                arch = inspect_model_architecture(model_dir)
                if arch["model_type"] == "7B":
                    cfg = json.loads((model_dir / "config.json").read_text())
                    if any(cfg.get(k) != v for k, v in ARCH_7B.items()) or cfg.get("model_type") != "qwen2":
                        violations.append("Cấu hình chưa khớp đầy đủ Qwen2.5 7B Instruct.")
                    quant = cfg.get("quantization", cfg.get("quantization_config", {}))
                    if quant.get("bits") != 4:
                        violations.append("Chỉ cho phép base 7B 4-bit đã xác minh; không suy từ tên thư mục.")
                    if not arch["has_weights"]:
                        violations.append(f"Thư mục {model_dir} có config 7B nhưng thiếu tệp trọng số model.safetensors.")
                    else:
                        model_ready = True
                else:
                    violations.append(f"Thư mục {model_dir} chứa mô hình {arch['model_type']}, không phải Qwen2.5-7B.")
            except Exception as e:
                violations.append(f"Không thể đọc cấu trúc mô hình tại {model_dir}: {e}")
        else:
            violations.append(f"Đường dẫn mô hình không tồn tại: {model_dir}")

    passed = len(violations) == 0

    return {
        "passed": passed,
        "eligible_for_training": passed and model_ready,
        "estimated_peak_memory_gb": round(estimated_peak_gb, 2),
        "required_available_memory_gb": round(estimated_peak_gb, 2),
        "is_empirical_measurement": False,
        "disclaimer": "Đây là ước lượng lý thuyết dựa trên cấu hình tham số, KHÔNG PHẢI cam kết an toàn tuyệt đối hay phép đo peak live của MLX.",
        "memory_info": mem,
        "recommended_config": {
            "batch_size": 1,
            "grad_checkpoint": True,
            "max_seq_length": min(max_seq_length, 1024),
            "num_layers": min(num_layers, 4),
            "learning_rate": 0.00002,
        },
        "model_ready": model_ready,
        "model_path": model_path_str,
        "violations": violations,
        "rationale": "Đạt ngưỡng ước lượng an toàn trên 16GB Mac (cần giám sát live)" if passed else "; ".join(violations),
    }


def audit_context_truncation(
    dataset_path: Path,
    max_seq_length: int = 1024,
    model_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """Audit dataset jsonl files for prompt + target token lengths using exact tokenizer.

    Fails closed if records are malformed JSON/schema, if valid.jsonl is missing,
    or if target tokens are truncated beyond threshold.
    """
    from app.token_auditor import audit_dataset_exact
    res = audit_dataset_exact(dataset_path, model_dir, max_seq_length)

    train_file = dataset_path / "train.jsonl"
    valid_file = dataset_path / "valid.jsonl"
    files_ok = train_file.exists() and valid_file.exists()

    violations = res.get("violations", [])
    train_malformed = sum(
        1 for v in violations
        if v.get("file") == "train.jsonl" and v.get("code") in ("MALFORMED_JSON", "INVALID_TYPE", "EMPTY_MESSAGES", "INVALID_MESSAGE_ITEM", "EMPTY_LINE", "UNSUPPORTED_SCHEMA")
    )
    valid_malformed = sum(
        1 for v in violations
        if v.get("file") == "valid.jsonl" and v.get("code") in ("MALFORMED_JSON", "INVALID_TYPE", "EMPTY_MESSAGES", "INVALID_MESSAGE_ITEM", "EMPTY_LINE", "UNSUPPORTED_SCHEMA")
    )

    res["acceptable"] = bool(files_ok and (not res.get("has_violations", False)) and res.get("status") == "SUCCESS")
    res["train"] = {"malformed_samples": train_malformed, "total_samples": res.get("valid_samples", 0)}
    res["valid"] = {"malformed_samples": valid_malformed, "total_samples": res.get("valid_samples", 0)}
    return res
