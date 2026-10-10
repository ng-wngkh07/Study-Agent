"""Launch a real MLX LoRA fine-tune, keeping the training environment separate."""

import argparse
import hashlib
import json
import logging
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from app.config import BASE_DIR, TRAINING_MODEL_DIR
from app.corrective_training import validate_corrective_trial
from app.gpu_lock import GPULockManager, gpu_coordinator
from app.memory_preflight import LiveMemoryMonitor, get_hardware_memory_profile
from app.run_ledger import (
    RunLedger, run_ledger,
    STATUS_CREATED, STATUS_PREFLIGHT, STATUS_RUNNING,
    STATUS_COMPLETED, STATUS_FAILED, STATUS_OOM,
    STATUS_REJECTED, STATUS_KILLED_ABNORMAL,
)

logger = logging.getLogger(__name__)


def verify_auxiliary_files(data_dir: Path, approval: dict):
    """Bind separately reviewed curriculum provenance to the approved run."""
    for name, expected in approval.get("auxiliary_files_sha256", {}).items():
        path = data_dir / name
        if path.resolve().parent != data_dir.resolve() or not path.is_file():
            raise ValueError("Tệp dữ liệu bổ sung không hợp lệ: " + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Dữ liệu bổ sung đã thay đổi sau khi duyệt: " + name)


def _get_active_ledger(data_dir: Path, explicit_ledger: Optional[RunLedger] = None) -> RunLedger:
    if explicit_ledger is not None:
        return explicit_ledger
    import app.config as cfg
    if BASE_DIR != cfg.BASE_DIR:
        runs_dir = BASE_DIR / "data" / "runs"
        return RunLedger(runs_dir=runs_dir, index_file=runs_dir / "index.jsonl")
    try:
        data_dir.resolve().relative_to(BASE_DIR.resolve())
    except ValueError:
        test_runs = data_dir.parent / "test_runs"
        return RunLedger(runs_dir=test_runs, index_file=test_runs / "index.jsonl")
    return run_ledger


def _stop_child_process_bounded(proc, timeout_sec: float = 5.0) -> Optional[int]:
    """Gracefully terminate child process with bounded wait, escalate to kill if necessary, and reap."""
    if not proc:
        return None
    try:
        if hasattr(proc, "poll") and proc.poll() is not None:
            return proc.returncode
    except Exception:
        pass

    try:
        if hasattr(proc, "terminate"):
            proc.terminate()
    except (ProcessLookupError, OSError):
        return getattr(proc, "returncode", None)
    except Exception:
        pass

    try:
        if hasattr(proc, "wait"):
            return proc.wait(timeout=timeout_sec)
    except (subprocess.TimeoutExpired, TypeError):
        pass
    except Exception:
        pass

    try:
        if hasattr(proc, "kill"):
            proc.kill()
    except (ProcessLookupError, OSError):
        return getattr(proc, "returncode", None)
    except Exception:
        pass

    try:
        if hasattr(proc, "wait"):
            return proc.wait(timeout=timeout_sec)
    except Exception:
        pass

    return getattr(proc, "returncode", None)


def train(data_dir: Path, iterations: int = 80, num_layers: int = 4,
          adapter_dir: Path | None = None, model_dir: Path | None = None,
          learning_rate: float = 0.00002,
          max_seq_length: int = 1024, coordinator: GPULockManager | None = None,
          evict_ollama: bool = True, ledger: Optional[RunLedger] = None,
          timeout_seconds: float = 3600.0):
    model_dir = model_dir or TRAINING_MODEL_DIR
    if adapter_dir is not None and not adapter_dir.is_absolute():
        adapter_dir = BASE_DIR / adapter_dir
    if not model_dir.is_absolute():
        model_dir = BASE_DIR / model_dir
    if not data_dir.is_absolute():
        data_dir = BASE_DIR / data_dir

    run_config = {
        "iterations": iterations,
        "num_layers": num_layers,
        "learning_rate": learning_rate,
        "max_seq_length": max_seq_length,
        "batch_size": 1,
        "grad_checkpoint": True,
        "mask_prompt": True,
    }

    # Step 1: Pre-allocate run in ledger BEFORE ANY file reading or gates!
    # If ledger cannot persist, must fail immediately without spawning MLX.
    active_ledger = _get_active_ledger(data_dir, ledger)
    run_record = active_ledger.create_run(
        config=run_config,
        base_model_dir=model_dir,
        dataset_dir=data_dir,
        dataset_sha256="pending_preflight",
        target_hypothesis=f"Sửa lỗi hành vi và duy trì chất lượng cho tập {data_dir.name}",
        baseline_metrics={},
        frozen_holdout_id=f"holdout-{data_dir.name}",
    )
    run_id = run_record["run_id"]

    monitor: Optional[LiveMemoryMonitor] = None
    proc: Optional[subprocess.Popen] = None
    terminal_status_set = False

    try:
        # Phase 1: Parameter checks
        if iterations < 1 or num_layers < 1 or not math.isfinite(learning_rate) or learning_rate <= 0 or max_seq_length < 1:
            raise ValueError("Số bước, số lớp và tốc độ học phải lớn hơn 0")

        # Phase 2: Source dataset checks & reading (inside try so unreadable files are recorded in ledger)
        train_file = data_dir / "train.jsonl"
        valid_file = data_dir / "valid.jsonl"
        if not train_file.is_file() or not valid_file.is_file():
            raise FileNotFoundError("Cần tạo train.jsonl và valid.jsonl bằng lệnh prepare-train trước")

        train_size = len(train_file.read_text(encoding="utf-8").splitlines())
        valid_size = len(valid_file.read_text(encoding="utf-8").splitlines())
        dataset_digest = hashlib.sha256(train_file.read_bytes() + valid_file.read_bytes()).hexdigest()

        approval_path = data_dir / "approval.json"
        if not approval_path.exists():
            raise ValueError("Bộ dữ liệu chưa có approval.json; cần duyệt dữ liệu trước khi huấn luyện")
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        if approval.get("dataset_sha256") != dataset_digest:
            raise ValueError("Dữ liệu đã thay đổi sau khi được duyệt; hãy kiểm tra và duyệt lại")
        verify_auxiliary_files(data_dir, approval)
        if approval.get("approved_manifest_sha256"):
            manifest = data_dir / "approved_manifest.jsonl"
            if not manifest.exists() or hashlib.sha256(manifest.read_bytes()).hexdigest() != approval["approved_manifest_sha256"]:
                raise ValueError("Manifest đã thay đổi sau khi duyệt; cần đối chiếu nguồn và duyệt lại")

        summary_path = data_dir / "summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if summary.get("audit_complete") is False:
                raise ValueError("Chưa kiểm tra xong dữ liệu; không được huấn luyện")
            cross_book_pairs = summary.get("cross_book_pairs", 0)
            training_cross_book_pairs = summary.get(
                "train_cross_book_pairs",
                cross_book_pairs - summary.get("skipped_cross_book_pairs_for_holdout", 0),
            )
            if cross_book_pairs and not training_cross_book_pairs:
                raise ValueError("Tất cả ví dụ liên sách đã bị loại khỏi tập học")
        if train_size < 8 or valid_size < 2:
            raise ValueError(f"Dữ liệu huấn luyện/kiểm tra quá ít: {train_size}/{valid_size}")
        if adapter_dir is None:
            raise ValueError("Cần --adapter-dir mới cho trial sửa lỗi; không dùng adapter đang phục vụ")
        if adapter_dir.exists() and any(adapter_dir.iterdir()):
            raise ValueError(f"Thư mục {adapter_dir} đã chứa adapter hoặc hồ sơ; chọn output mới")
        if not (model_dir / "config.json").exists():
            raise FileNotFoundError(f"Chưa tải mô hình MLX vào {model_dir}")

        # Bind verified dataset hashes & baseline into ledger record
        baseline_metrics = {"train_size": train_size, "valid_size": valid_size}
        target_hypothesis = f"Sửa lỗi hành vi và duy trì chất lượng cho tập {data_dir.name}"
        frozen_holdout_id = f"holdout-{data_dir.name}"
        plan_path = data_dir / "trial_plan.json"
        if plan_path.is_file():
            try:
                plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
                evidence = plan_data.get("evidence", {})
                b_info = evidence.get("baseline", {})
                b_path = Path(b_info.get("path", ""))
                if not b_path.is_file():
                    if (data_dir / b_path).is_file():
                        b_path = data_dir / b_path
                    elif (BASE_DIR / b_path).is_file():
                        b_path = BASE_DIR / b_path
                if b_path.is_file():
                    b_rep = json.loads(b_path.read_text(encoding="utf-8"))
                    baseline_metrics["baseline_report_sha256"] = b_info.get("sha256")
                    baseline_metrics["production_model"] = b_rep.get("production_model")
                    baseline_metrics["production_digest"] = b_rep.get("production_digest")
                    baseline_metrics["suite_sha256"] = b_rep.get("suite_sha256")
                    baseline_metrics["scores"] = b_rep.get("scores") or b_rep.get("per_error")
                    baseline_metrics["content_review_complete"] = b_rep.get("content_review_complete")
                    if b_rep.get("suite_sha256"):
                        frozen_holdout_id = b_rep["suite_sha256"]
                proto_info = evidence.get("evaluation_protocol", {})
                if proto_info:
                    baseline_metrics["evaluation_protocol_sha256"] = proto_info.get("sha256")
                    proto_path = Path(proto_info.get("path", ""))
                    if not proto_path.is_file():
                        if (data_dir / proto_path).is_file():
                            proto_path = data_dir / proto_path
                        elif (BASE_DIR / proto_path).is_file():
                            proto_path = BASE_DIR / proto_path
                    if proto_path.is_file():
                        proto_rep = json.loads(proto_path.read_text(encoding="utf-8"))
                        suite_info = proto_rep.get("suite", {})
                        if isinstance(suite_info, dict) and suite_info.get("sha256"):
                            frozen_holdout_id = suite_info["sha256"]
                        elif proto_rep.get("frozen_holdout_id"):
                            frozen_holdout_id = proto_rep["frozen_holdout_id"]
            except Exception as e:
                logger.warning(f"Không thể nạp baseline metrics đầy đủ từ trial_plan: {e}")

        # Phase 2b: Bind verified dataset manifest & baseline into ledger record
        target_hypothesis = f"Sửa lỗi hành vi và duy trì chất lượng cho tập {data_dir.name}"
        if plan_path.is_file():
            try:
                target_hypothesis = plan_data.get("hypothesis") or target_hypothesis
            except Exception:
                pass

        if hasattr(active_ledger, "bind_verified_manifest"):
            active_ledger.bind_verified_manifest(
                run_id=run_id,
                config=run_config,
                base_model_dir=model_dir,
                dataset_dir=data_dir,
                dataset_sha256=dataset_digest,
                target_hypothesis=target_hypothesis,
                baseline_metrics=baseline_metrics,
                frozen_holdout_id=frozen_holdout_id,
            )

        # Phase 3: Preflight checks
        active_ledger.update_status(run_id, STATUS_PREFLIGHT)

        from app.preflight_7b import inspect_model_architecture
        arch_info = inspect_model_architecture(model_dir)
        model_type = arch_info.get("model_type")

        trial = validate_corrective_trial(data_dir, model_dir, adapter_dir, approval, run_config)

        if model_type == "7B":
            from app.preflight_7b import preflight_check_7b_training
            pre = preflight_check_7b_training(model_dir=model_dir, batch_size=1,
                                              num_layers=num_layers, max_seq_length=max_seq_length,
                                              grad_checkpoint=True)
        else:
            from app.memory_preflight import preflight_check_memory_training
            pre = preflight_check_memory_training(model_dir=model_dir, dataset_dir=data_dir,
                                                  batch_size=1, num_layers=num_layers,
                                                  max_seq_length=max_seq_length,
                                                  grad_checkpoint=True)

        if not pre.get("eligible_for_training"):
            raise RuntimeError(f"CHẶN HUẤN LUYỆN: {pre.get('violations')}")

        # Read the live corpus before preparing output or acquiring any GPU lock.
        from app.corpus_readiness import require_complete_corpus
        require_complete_corpus(BASE_DIR)
        from app.corpus_scope import verify_dataset_scope
        verify_dataset_scope(data_dir, root=BASE_DIR)
        from app.dataset_balance import require_balanced_dataset
        require_balanced_dataset(BASE_DIR, data_dir, model_dir)

        python = BASE_DIR / ".train-venv" / "bin" / "python"
        if not python.exists():
            raise FileNotFoundError("Chưa cài .train-venv với mlx-lm")

        # Phase 4: Training execution setup
        adapter_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = adapter_dir / "training.log"

        command = [
            str(python), "-m", "mlx_lm.lora",
            "--model", str(model_dir),
            "--train", "--data", str(data_dir),
            "--adapter-path", str(adapter_dir),
            "--fine-tune-type", "lora",
            "--mask-prompt",
            "--batch-size", "1",
            "--num-layers", str(num_layers),
            "--iters", str(iterations),
            "--learning-rate", str(learning_rate),
            "--max-seq-length", str(max_seq_length),
            "--grad-checkpoint",
            "--steps-per-report", "5",
            "--steps-per-eval", str(max(10, min(40, iterations))),
            "--save-every", str(max(10, min(40, iterations))),
        ]
        print(json.dumps({"train_examples": train_size, "valid_examples": valid_size, "command": command}, ensure_ascii=False), flush=True)

        extra_info = {
            "data_version": data_dir.name,
            "iterations": iterations,
            "num_layers": num_layers,
            "learning_rate": learning_rate,
            "adapter_dir": str(adapter_dir),
            "corrective_trial": trial,
            "run_id": run_id,
        }
        if coordinator is None:
            runtime_dir = BASE_DIR / "data" / "runtime"
            coordinator = GPULockManager(
                lock_path=runtime_dir / "gpu.lock",
                state_path=runtime_dir / "gpu_state.json",
                intent_path=runtime_dir / "gpu_intent.lock",
            )

        active_ledger.update_status(run_id, STATUS_RUNNING)

        def abort_cb(reason: str):
            if proc and hasattr(proc, "terminate"):
                try:
                    proc.terminate()
                except Exception:
                    pass

        def mem_telemetry_cb(avail_gb, swap_mb):
            if run_id:
                try:
                    hw_total = None
                    try:
                        hw_total = get_hardware_memory_profile().get("total_gb")
                    except Exception:
                        pass
                    sys_used_mb = (
                        round((hw_total - avail_gb) * 1024, 1)
                        if (hw_total and hw_total > 0 and avail_gb is not None)
                        else None
                    )
                    mlx_rss_mb = None
                    if proc and getattr(proc, "pid", None):
                        try:
                            rss_out = subprocess.check_output(
                                ["ps", "-p", str(proc.pid), "-o", "rss="],
                                text=True, stderr=subprocess.DEVNULL
                            )
                            if rss_out.strip():
                                mlx_rss_mb = round(int(rss_out.strip()) / 1024.0, 1)
                        except Exception:
                            pass
                    active_ledger.update_status(
                        run_id, STATUS_RUNNING,
                        system_used_mb=sys_used_mb,
                        peak_memory_mb=mlx_rss_mb,
                        peak_swap_mb=round(swap_mb, 1) if swap_mb is not None else None,
                    )
                except Exception:
                    pass

        monitor = LiveMemoryMonitor(
            check_interval_sec=1.5,
            abort_callback=abort_cb,
            telemetry_callback=mem_telemetry_cb,
        )
        monitor.start()

        with coordinator.acquire_for_training(timeout=60.0, extra_info=extra_info, evict_ollama=evict_ollama) as lock_info:
            fds = getattr(lock_info, "fds", (int(lock_info),))
            with open(log_file_path, "w", encoding="utf-8") as log_file:
                proc = subprocess.Popen(command, cwd=BASE_DIR, pass_fds=fds, stdout=log_file, stderr=subprocess.STDOUT)
                coordinator.update_child_pid(proc.pid)
                active_ledger.update_child_pid(run_id, proc.pid)

                import time as _t
                start_time = _t.time()
                from app.training_telemetry import TrainingTelemetry
                telemetry = TrainingTelemetry(active_ledger, run_id, log_file_path, adapter_dir)

                def sync_loss_telemetry():
                    telemetry.poll()

                try:
                    if hasattr(proc, "poll"):
                        returncode = None
                        while returncode is None:
                            returncode = proc.poll()
                            sync_loss_telemetry()
                            if returncode is not None:
                                break
                            if _t.time() - start_time > timeout_seconds:
                                raise subprocess.TimeoutExpired(command, timeout_seconds)
                            _t.sleep(0.5)
                    else:
                        try:
                            returncode = proc.wait(timeout=timeout_seconds)
                        except TypeError:
                            returncode = proc.wait()
                        sync_loss_telemetry()
                except subprocess.TimeoutExpired:
                    sync_loss_telemetry()
                    actual_rc = _stop_child_process_bounded(proc)
                    (adapter_dir / "orchestration_checkpoint.json").write_text(json.dumps({
                        "status": "timed_out", "child_pid": getattr(proc, "pid", None),
                        "return_code": actual_rc,
                        "error_type": "TimeoutExpired", "automatic_stop_sent": True,
                        "trial": trial, "requires_process_and_artifact_readback": True,
                    }, ensure_ascii=False, indent=2), encoding="utf-8")
                    active_ledger.update_status(
                        run_id, STATUS_FAILED,
                        diagnosis=f"Tiến trình huấn luyện quá hạn ({timeout_seconds}s)",
                        return_code=actual_rc,
                        decision="TIMEOUT_EXPIRED",
                    )
                    terminal_status_set = True
                    raise
                except (KeyboardInterrupt, SystemExit) as exc:
                    sync_loss_telemetry()
                    actual_rc = _stop_child_process_bounded(proc)
                    (adapter_dir / "orchestration_checkpoint.json").write_text(json.dumps({
                        "status": "interrupted_by_signal", "child_pid": getattr(proc, "pid", None),
                        "return_code": actual_rc or -9,
                        "error_type": type(exc).__name__, "automatic_stop_sent": True,
                        "trial": trial, "requires_process_and_artifact_readback": True,
                    }, ensure_ascii=False, indent=2), encoding="utf-8")
                    active_ledger.update_status(
                        run_id, STATUS_KILLED_ABNORMAL,
                        diagnosis=f"Tiến trình bị gián đoạn tín hiệu: {type(exc).__name__}",
                        return_code=actual_rc or -9,
                        decision="INTERRUPTED_BY_SIGNAL",
                    )
                    terminal_status_set = True
                    raise
                except BaseException as exc:
                    sync_loss_telemetry()
                    actual_rc = _stop_child_process_bounded(proc)
                    auto_stop = True
                    status_str = "interrupted_by_exception"

                    (adapter_dir / "orchestration_checkpoint.json").write_text(json.dumps({
                        "status": status_str, "child_pid": getattr(proc, "pid", None),
                        "return_code": actual_rc,
                        "error_type": type(exc).__name__, "automatic_stop_sent": auto_stop,
                        "trial": trial, "requires_process_and_artifact_readback": True,
                    }, ensure_ascii=False, indent=2), encoding="utf-8")
                    active_ledger.update_status(
                        run_id, STATUS_KILLED_ABNORMAL,
                        diagnosis=f"Tiến trình bị gián đoạn/ngoại lệ: {type(exc).__name__}: {exc}",
                        return_code=actual_rc if actual_rc is not None else -9,
                        decision="RUNNER_INTERRUPTED_ABNORMAL",
                    )
                    terminal_status_set = True
                    raise

        mem_stats = monitor.stop()
        monitor = None
        with (adapter_dir / "memory_monitor.json").open("x", encoding="utf-8") as stream:
            json.dump(mem_stats, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        sync_loss_telemetry()

        telemetry.poll(final=True)

        if mem_stats.get("abort_triggered"):
            active_ledger.update_status(
                run_id, STATUS_OOM,
                diagnosis=mem_stats.get("abort_reason"),
                peak_swap_mb=mem_stats.get("peak_swap_used_mb"),
                decision="ABORTED_MEMORY_PRESSURE",
            )
            terminal_status_set = True
            raise RuntimeError(f"Dừng khẩn cấp do bộ nhớ: {mem_stats.get('abort_reason')}")

        if returncode != 0:
            if mem_stats.get("abort_triggered"):
                status = STATUS_OOM
                decision = "ABORTED_MEMORY_PRESSURE"
                diagnosis = f"Dừng do áp lực bộ nhớ (mã {returncode}): {mem_stats.get('abort_reason')}"
            elif returncode in (-9, 137):
                status = STATUS_KILLED_ABNORMAL
                decision = "KILLED_BY_SIGNAL_WITHOUT_OOM_EVIDENCE"
                diagnosis = f"MLX bị dừng bởi tín hiệu SIGKILL (mã {returncode}); telemetry không ghi nhận OOM rõ ràng"
            else:
                status = STATUS_FAILED
                decision = f"TERMINATED_{status}"
                diagnosis = f"MLX fine-tune thất bại (mã {returncode})"

            active_ledger.update_status(
                run_id, status,
                diagnosis=diagnosis,
                return_code=returncode,
                peak_swap_mb=mem_stats.get("peak_swap_used_mb"),
                decision=decision,
            )
            terminal_status_set = True
            raise RuntimeError(diagnosis)

        # Phase 5: Post-training validation
        if not (adapter_dir / "adapters.safetensors").exists():
            raise RuntimeError("MLX kết thúc nhưng không tìm thấy adapter đã lưu")
        if hashlib.sha256(train_file.read_bytes() + valid_file.read_bytes()).hexdigest() != dataset_digest:
            raise RuntimeError("Dữ liệu thay đổi trong lúc huấn luyện; adapter cần được đánh giá lại")
        if approval.get("approved_manifest_sha256") and hashlib.sha256(
            (data_dir / "approved_manifest.jsonl").read_bytes()
        ).hexdigest() != approval["approved_manifest_sha256"]:
            raise RuntimeError("Manifest nguồn thay đổi trong lúc huấn luyện; không được dùng adapter")
        verify_auxiliary_files(data_dir, approval)
        if validate_corrective_trial(data_dir, model_dir, adapter_dir, approval, run_config) != trial:
            raise RuntimeError("Hồ sơ trial/base đã đổi trong lúc huấn luyện; không được dùng adapter")

        if train_size >= 20 and valid_size >= 2 and iterations >= 40:
            (adapter_dir / "ready.json").write_text(
                json.dumps({"train_examples": train_size, "valid_examples": valid_size, "iterations": iterations, "learning_rate": learning_rate, "max_seq_length": max_seq_length, "dataset_sha256": dataset_digest, "data_version": data_dir.name, "corrective_trial": trial, "quality_status": "unreviewed_not_promoted"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if adapter_dir.exists():
            for p in sorted(adapter_dir.glob("*.safetensors")):
                step_m = re.search(r"(\d+)", p.name)
                step_num = int(step_m.group(1)) if step_m else iterations
                active_ledger.record_checkpoint(run_id, step=step_num, checkpoint_path=p)

        active_ledger.update_status(
            run_id, STATUS_COMPLETED,
            return_code=0,
            peak_swap_mb=mem_stats.get("peak_swap_used_mb"),
            decision="TRIAL_SUCCESSFUL",
        )
        terminal_status_set = True

    except BaseException as err:
        if monitor:
            try:
                monitor.stop()
            except Exception:
                pass
        if not terminal_status_set:
            status_to_record = STATUS_KILLED_ABNORMAL if isinstance(err, (KeyboardInterrupt, SystemExit)) else STATUS_REJECTED
            err_msg = str(err)
            if any(term in err_msg.lower() for term in ("gpu", "timeout", "lock", "popen")):
                status_to_record = STATUS_FAILED
            elif any(term in err_msg.lower() for term in ("thất bại", "đổi trong lúc", "không tìm thấy adapter")):
                status_to_record = STATUS_FAILED

            active_ledger.update_status(
                run_id, status_to_record,
                diagnosis=err_msg or type(err).__name__,
                decision=f"TERMINATED_{status_to_record}",
            )
            terminal_status_set = True
        raise


def main():
    parser = argparse.ArgumentParser(description="Huấn luyện LoRA cục bộ trên Apple Silicon")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--iters", type=int, required=True)
    parser.add_argument("--num-layers", type=int, required=True)
    parser.add_argument("--adapter-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=TRAINING_MODEL_DIR)
    parser.add_argument("--learning-rate", type=float, required=True)
    parser.add_argument("--max-seq-length", type=int, required=True)
    args = parser.parse_args()
    train(
        args.data,
        args.iters,
        args.num_layers,
        args.adapter_dir,
        model_dir=args.model_dir,
        learning_rate=args.learning_rate,
        max_seq_length=args.max_seq_length
    )


if __name__ == "__main__":
    main()
