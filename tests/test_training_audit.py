import hashlib
import json

from app.training_audit import audit, check_record


def test_verifier_requests_one_boolean_per_answer(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": '{"translation_ok":true,"approved":[true]}'}}

    def fake_post(url, json, timeout):
        captured.update(json)
        return Response()

    monkeypatch.setattr("app.training_audit.requests.post", fake_post)
    record = {
        "pair": {"title": "Sách", "sources": [
            {"id": "S1", "page": 1, "text": "First source."},
            {"id": "S2", "page": 2, "text": "Second source."},
        ]},
        "language": "en", "translations": {"S1": "Nguồn một.", "S2": "Nguồn hai."},
        "items": [{"question": "Vì sao?", "answer": "Vì hai nguồn. [S1] [S2]"}],
    }
    result = check_record(record, model="qwen3:4b")
    assert result["decisions"] == [{"supported": True, "reason": ""}]
    assert captured["format"]["properties"]["approved"]["minItems"] == 1
    assert captured["format"]["properties"]["approved"]["maxItems"] == 1


def test_incomplete_audit_does_not_approve_training(tmp_path, monkeypatch):
    record = {
        "key": "example",
        "pair": {
            "filename": "book.pdf", "title": "Sách thử nghiệm",
            "sources": [
                {"id": "S1", "page": 1, "text": "Nội dung thứ nhất"},
                {"id": "S2", "page": 2, "text": "Nội dung thứ hai"},
            ],
        },
        "language": "vi", "translations": {},
        "items": [{"question": "Hai đoạn nói gì?", "answer": "Hai đoạn mô tả vấn đề. [S1] [S2]"}],
    }
    (tmp_path / "manifest.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n")
    (tmp_path / "approval.json").write_text("stale")

    def unavailable(*_args, **_kwargs):
        raise ValueError("Verifier unavailable")

    monkeypatch.setattr("app.training_audit.check_record", unavailable)
    summary = audit(tmp_path, model="qwen3:4b")
    assert summary["audit_complete"] is False
    assert summary["reviewed_records"] == 0
    assert not (tmp_path / "approval.json").exists()


def test_cached_approval_cannot_pass_invalid_translation(tmp_path):
    chinese = "为什么类别是有用的，但定义不起作用？通过相似性确定类别，使用原型或实例。"
    english = "The mind and the body respond to trauma, and the nervous system changes with experience. " * 4
    record = {
        "key": "bad-translation",
        "pair": {
            "filename": "english-book.pdf", "title": "English book",
            "sources": [
                {"id": "S1", "page": 1, "text": english},
                {"id": "S2", "page": 2, "text": english},
            ],
        },
        "language": "en", "translations": {"S1": chinese, "S2": chinese},
        "items": [{"question": "Hai đoạn nói gì?", "answer": "Hai đoạn mô tả vấn đề. [S1] [S2]"}],
    }
    (tmp_path / "manifest.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n")
    key = hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    cached = {
        "key": key, "record_key": record["key"], "translation_ok": True,
        "decisions": [{"supported": True, "reason": ""}],
    }
    (tmp_path / "audit.jsonl").write_text(json.dumps(cached, ensure_ascii=False) + "\n")

    summary = audit(tmp_path)

    assert summary["audit_complete"] is True
    assert summary["rejected_basic_quality_records"] == 1
    assert (tmp_path / "approved_manifest.jsonl").read_text() == ""
