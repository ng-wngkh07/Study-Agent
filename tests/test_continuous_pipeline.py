"""Comprehensive test suite for ContinuousPipelineOrchestrator:
Verifies:
1. Concurrent start serialization (only 1 owner permitted)
2. Fail-closed behavior on corrupted state (restores from .bak or raises CorruptStateError)
3. Wrong PID / identity mismatch fails closed without signaling
4. Child / process group management in pause and stop with safe session isolation
5. complete_round enforces exit code 0 and non-empty evaluation evidence
6. Crash resume idempotency (resumes from checkpoint without duplicating trials)
7. At least 3 full simulated cycles without artificial trial caps
"""

import concurrent.futures
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import pytest

from app.pipeline_orchestrator import ContinuousPipelineOrchestrator, CorruptStateError


@pytest.fixture
def temp_orchestrator(tmp_path):
    state_file = tmp_path / "test_pipeline_state.json"
    lock_file = tmp_path / "test_pipeline.lock"
    return ContinuousPipelineOrchestrator(state_path=state_file, lock_path=lock_file)


def test_initial_state_is_idle(temp_orchestrator):
    status = temp_orchestrator.get_status()
    assert status["status"] == "idle"
    assert status["round"] == 0
    assert status["pid"] is None


def test_concurrent_start_enforces_single_owner(temp_orchestrator, tmp_path):
    """Two concurrent starts under exclusive lock: only one wins, the other raises RuntimeError."""
    cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
    proc1 = subprocess.Popen(cmd, start_new_session=True, cwd=str(tmp_path))
    proc2 = subprocess.Popen(cmd, start_new_session=True, cwd=str(tmp_path))

    success_count = 0
    error_count = 0

    def attempt_start(proc):
        nonlocal success_count, error_count
        try:
            temp_orchestrator.start_round("v6", cmd, 100, cwd=tmp_path, mock_proc=proc)
            success_count += 1
        except RuntimeError:
            error_count += 1

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(attempt_start, proc1), executor.submit(attempt_start, proc2)]
            for f in futures:
                f.result()

        assert success_count == 1
        assert error_count == 1
    finally:
        try:
            proc1.terminate()
            proc2.terminate()
            proc1.wait(timeout=2)
            proc2.wait(timeout=2)
        except OSError:
            pass
        temp_orchestrator.stop()


def test_corrupt_state_fails_closed_or_recovers_backup(temp_orchestrator, tmp_path):
    """Corrupted state file must raise CorruptStateError if no valid backup, or recover from .bak."""
    temp_orchestrator.state_path.write_text("{corrupt-json", encoding="utf-8")
    with pytest.raises(CorruptStateError, match="bị hỏng"):
        temp_orchestrator.get_status()

    # Valid backup recovery
    valid_state = {"status": "idle", "round": 2, "history": []}
    bak_path = temp_orchestrator.state_path.with_suffix(".json.bak")
    bak_path.write_text(json.dumps(valid_state), encoding="utf-8")

    recovered = temp_orchestrator.get_status()
    assert recovered["round"] == 2
    assert recovered["status"] == "idle"


def test_wrong_pid_identity_fails_closed(temp_orchestrator, tmp_path):
    """If PID exists but command or cwd does not match, _verify_process_alive must return False."""
    cmd = [sys.executable, "-c", "import time; time.sleep(5)"]
    proc = subprocess.Popen(cmd, start_new_session=True, cwd=str(tmp_path))
    try:
        temp_orchestrator.start_round("v6", cmd, 50, cwd=tmp_path, mock_proc=proc)

        # Tamper expected_command in state to simulate mismatched PID
        state = temp_orchestrator._read_state()
        state["command"] = ["completely_unrelated_executable"]
        temp_orchestrator._write_state(state)

        # Verification must fail closed
        alive = temp_orchestrator._verify_process_alive(
            pid=proc.pid,
            expected_command=["completely_unrelated_executable"],
            expected_cwd=str(tmp_path)
        )
        assert not alive

        with pytest.raises(RuntimeError, match="not alive or identity mismatch"):
            temp_orchestrator.pause()
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except OSError:
            pass
        temp_orchestrator.stop()


def test_child_process_group_management_in_pause_and_stop(temp_orchestrator, tmp_path):
    """A parent launching a child process must have both parent and child paused and stopped cleanly."""
    child_pid_file = tmp_path / "child.pid"
    parent_script = (
        "import subprocess, sys, time\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        f"with open(r'{child_pid_file}', 'w') as f:\n"
        "    f.write(str(child.pid) + '\\n')\n"
        "    f.flush()\n"
        "child.wait()\n"
    )
    cmd = [sys.executable, "-c", parent_script]
    proc = subprocess.Popen(cmd, start_new_session=True, cwd=str(tmp_path))

    # Wait for child process to spawn and write its PID
    child_pid = None
    for _ in range(30):
        if child_pid_file.exists():
            content = child_pid_file.read_text().strip()
            if content.isdigit():
                child_pid = int(content)
                break
        time.sleep(0.1)

    assert child_pid is not None, "Child process failed to write PID"
    # Verify child is alive initially
    os.kill(child_pid, 0)

    try:
        temp_orchestrator.start_round("v6", cmd, 100, cwd=tmp_path, mock_proc=proc)
        state = temp_orchestrator.get_status()
        assert state["status"] == "running"

        # Pause entire group
        temp_orchestrator.pause("Pause test")
        assert temp_orchestrator.get_status()["status"] == "paused"

        # Resume entire group
        temp_orchestrator.resume()
        assert temp_orchestrator.get_status()["status"] == "running"

        # Stop entire process group
        temp_orchestrator.stop(timeout=3.0)
        final_state = temp_orchestrator.get_status()
        assert final_state["status"] == "stopped"
        assert final_state["pid"] is None

        # Verify parent is dead
        assert proc.poll() is not None

        # STRICT ASSERTION: child process MUST be terminated
        time.sleep(0.3)
        with pytest.raises((ProcessLookupError, OSError)):
            os.kill(child_pid, 0)
    finally:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            pass
        try:
            os.kill(child_pid, signal.SIGKILL)
        except OSError:
            pass


def test_complete_round_validation(temp_orchestrator, tmp_path):
    """complete_round must reject non-zero exit code or missing evaluation evidence."""
    cmd = [sys.executable, "-c", "import sys; sys.exit(0)"]
    proc = subprocess.Popen(cmd, start_new_session=True, cwd=str(tmp_path))
    proc.wait(timeout=2)

    temp_orchestrator.start_round("v6", cmd, 40, cwd=tmp_path, mock_proc=proc)

    # Rejects non-zero exit code
    with pytest.raises(ValueError, match="mã lỗi 1"):
        temp_orchestrator.complete_round(exit_code=1, evaluation_evidence={"val_loss": 2.1})

    # Rejects empty evaluation evidence
    with pytest.raises(ValueError, match="bằng chứng evaluation"):
        temp_orchestrator.complete_round(exit_code=0, evaluation_evidence={})

    # Accepts exit_code 0 with valid evaluation evidence
    completed = temp_orchestrator.complete_round(
        exit_code=0,
        evaluation_evidence={"val_loss": 1.82, "grounded_citations": 12},
        adapter_path="data/adapters/trial-1"
    )
    assert completed["status"] == "completed"
    assert len(completed["history"]) == 1
    assert completed["history"][0]["evaluation"]["val_loss"] == 1.82


def test_crash_resume_idempotent_no_duplicate(temp_orchestrator, tmp_path):
    """Crash resume should preserve round count, checkpoints, and history without duplicating."""
    cmd = [sys.executable, "-c", "import sys; sys.exit(0)"]
    proc = subprocess.Popen(cmd, start_new_session=True, cwd=str(tmp_path))
    proc.wait(timeout=2)
    temp_orchestrator.start_round("v6", cmd, 40, cwd=tmp_path, mock_proc=proc)
    temp_orchestrator.record_checkpoint(20, "checkpoints/r1_s20", {"loss": 2.0})
    temp_orchestrator.complete_round(exit_code=0, evaluation_evidence={"val_loss": 1.9})

    cmd2 = [sys.executable, "-c", "import time; time.sleep(1)"]
    proc2 = subprocess.Popen(cmd2, start_new_session=True, cwd=str(tmp_path))
    proc2.wait(timeout=2)
    temp_orchestrator.start_round("v6", cmd2, 80, cwd=tmp_path, mock_proc=proc2)
    temp_orchestrator.record_checkpoint(40, "checkpoints/r2_s40", {"loss": 1.8})

    status = temp_orchestrator.get_status()
    assert status["status"] == "stopped"
    assert status["round"] == 2
    assert len(status["checkpoints"]) == 2
    assert len(status["history"]) == 1


def test_three_continuous_cycles_without_cap(temp_orchestrator, tmp_path):
    """Execute at least 3 full simulated cycles to prove no hard-coded 2-trial limit exists."""
    for cycle in range(1, 4):
        cmd = [sys.executable, "-c", "import time; time.sleep(5)"]
        proc = subprocess.Popen(cmd, start_new_session=True, cwd=str(tmp_path))
        try:
            state = temp_orchestrator.start_round(
                dataset_version=f"v6-cycle{cycle}",
                command=cmd,
                total_steps=80,
                cwd=tmp_path,
                mock_proc=proc
            )
            assert state["round"] == cycle
            assert state["status"] == "running"

            temp_orchestrator.record_checkpoint(
                step=40,
                checkpoint_path=f"data/checkpoints/cycle{cycle}/step40",
                metrics={"val_loss": 1.85 - (cycle * 0.05)}
            )

            # Pause & Resume cycle
            temp_orchestrator.pause()
            assert temp_orchestrator.get_status()["status"] == "paused"
            temp_orchestrator.resume()
            assert temp_orchestrator.get_status()["status"] == "running"

            proc.terminate()
            proc.wait(timeout=2)

            temp_orchestrator.complete_round(
                exit_code=0,
                evaluation_evidence={"final_val_loss": 1.80 - (cycle * 0.05), "passed_eval": True},
                adapter_path=f"data/adapters/cycle{cycle}"
            )
            final_status = temp_orchestrator.get_status()
            assert final_status["status"] == "completed"
            assert len(final_status["history"]) == cycle
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except OSError:
                pass

    final_state = temp_orchestrator.get_status()
    assert final_state["round"] == 3
    assert len(final_state["history"]) == 3
    assert [h["round"] for h in final_state["history"]] == [1, 2, 3]
