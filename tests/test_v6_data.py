import hashlib
import json

import pytest

from app.fine_tune import verify_auxiliary_files
from app.prepare_v6 import curriculum


def test_formal_curriculum_never_uses_established_bayes_benchmark():
    samples = curriculum()
    assert len({s["messages"][1]["content"] for s in samples}) == len(samples)
    probabilities = [s for s in samples if s["kind"] == "conditional_probability"]
    assert len(probabilities) >= 8
    for s in probabilities:
        d = s["derivation"]
        assert (d["total"], d["target"], d["true_flag"], d["false_flag"]) != (10000, 100, 90, 495)
        assert d["posterior_percent"] == pytest.approx(100*d["true_flag"]/(d["true_flag"]+d["false_flag"]))
        assert s["provenance"].startswith("Codex-authored hypothetical")


def test_auxiliary_provenance_hash_is_required_before_and_after_training(tmp_path):
    file = tmp_path/"curriculum_manifest.jsonl"
    file.write_text(json.dumps({"review": "complete"}))
    approval = {"auxiliary_files_sha256": {file.name: hashlib.sha256(file.read_bytes()).hexdigest()}}
    verify_auxiliary_files(tmp_path, approval)
    file.write_text("modified")
    with pytest.raises(ValueError, match="đã thay đổi"):
        verify_auxiliary_files(tmp_path, approval)


def test_auxiliary_file_cannot_escape_dataset(tmp_path):
    with pytest.raises(ValueError, match="không hợp lệ"):
        verify_auxiliary_files(tmp_path, {"auxiliary_files_sha256": {"../file": "hash"}})
