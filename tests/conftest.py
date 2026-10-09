"""Keep mocked app tests independent of a real training job on this host.

Retain the real coordinator/lock behavior inside each test's temporary directory;
never read, heal, or alter a production job's lock/state from fixture tests.
"""
import pytest


@pytest.fixture(autouse=True)
def isolated_default_gpu_coordinator(tmp_path, monkeypatch):
    from app.gpu_lock import gpu_coordinator
    runtime = tmp_path/'app-gpu-coordination'
    runtime.mkdir()
    monkeypatch.setattr(gpu_coordinator, 'lock_path', runtime/'gpu.lock')
    monkeypatch.setattr(gpu_coordinator, 'state_path', runtime/'gpu_state.json')
    monkeypatch.setattr(gpu_coordinator, 'intent_path', runtime/'gpu_intent.lock')
