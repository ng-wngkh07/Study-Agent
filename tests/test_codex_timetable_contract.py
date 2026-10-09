"""Independent acceptance contracts: no personal schedule is used as training data."""
import base64
import json
from contextlib import nullcontext
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app import server


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TIMETABLE_DB_PATH", str(tmp_path / "timetable.db"))
    monkeypatch.setenv("TIMETABLE_IMAGES_DIR", str(tmp_path / "images"))
    return TestClient(server.app)


def test_timetable_is_available_and_empty_on_fresh_store(client):
    response = client.get("/api/timetable")
    assert response.status_code == 200, response.text
    assert response.json()["entries"] == []


def test_image_payload_is_validated_before_model_call(client):
    response = client.post("/api/timetable/extract", json={
        "filename": "schedule.png", "image_base64": base64.b64encode(b"not an image").decode()
    })
    assert response.status_code == 400, response.text


def test_confirmation_cannot_invent_or_bypass_a_missing_draft(client):
    response = client.post("/api/timetable/confirm", json={
        "draft_id": "0" * 32,
        "entries": [{"course": "Linear algebra", "weekday": 1,
                     "start_time": "08:00", "end_time": "09:30", "room": "A101"}]
    })
    assert response.status_code == 404, response.text


def test_export_needs_explicit_date_range(client):
    response = client.get("/api/timetable/export.ics")
    assert response.status_code == 422, response.text


@pytest.mark.parametrize("entry", [
    {"course": "Math", "weekday": 0, "start_time": "08:00", "end_time": "09:00"},
    {"course": "Math", "weekday": 8, "start_time": "08:00", "end_time": "09:00"},
    {"course": "Math", "weekday": 1, "start_time": "25:00", "end_time": "26:00"},
    {"course": "Math", "weekday": 1, "start_time": "09:00", "end_time": "08:00"},
    {"course": "Math", "weekday": 1, "start_time": "08:00", "end_time": "08:00"},
    {"course": "  ", "weekday": 1, "start_time": "08:00", "end_time": "09:00"},
])
def test_invalid_manual_schedule_is_rejected_without_writing(client, entry):
    response = client.post("/api/timetable/manual", json=entry)
    assert response.status_code in (400, 422), response.text
    assert client.get("/api/timetable").json()["entries"] == []


def test_unknown_image_weekday_is_not_invented_as_monday():
    from app.timetable_vision import normalize_weekday
    assert normalize_weekday(None) is None
    assert normalize_weekday("không rõ") is None
    assert normalize_weekday("1") == 1
    assert normalize_weekday("2") == 2
    assert normalize_weekday("Thứ 2") == 1
    assert normalize_weekday("13") is None


def test_empty_confirmation_cannot_erase_an_existing_schedule(client):
    from app import timetable_store
    original = {"course": "Physics", "weekday": 2, "start_time": "10:00", "end_time": "11:00"}
    assert client.post("/api/timetable/manual", json=original).status_code == 200
    timetable_store.save_draft("a" * 32, "b" * 64, "test.png", [], [])
    response = client.post("/api/timetable/confirm", json={"draft_id": "a" * 32, "entries": []})
    assert response.status_code in (400, 422), response.text
    assert client.get("/api/timetable").json()["entries"][0]["course"] == "Physics"


def test_overlapping_manual_schedule_requires_resolution(client):
    first = {"course": "Math", "weekday": 1, "start_time": "08:00", "end_time": "09:30"}
    second = {"course": "Physics", "weekday": 1, "start_time": "09:00", "end_time": "10:00"}
    assert client.post("/api/timetable/manual", json=first).status_code == 200
    response = client.post("/api/timetable/manual", json=second)
    assert response.status_code in (409, 422), response.text
    assert len(client.get("/api/timetable").json()["entries"]) == 1


def fake_vision(monkeypatch, output, done_reason="stop", digest="d" * 64):
    from app import timetable_vision as vision
    tag_response = SimpleNamespace(status_code=200, json=lambda: {"models": [
        {"name": "qwen2.5vl:3b", "digest": digest}
    ]})
    model_response = SimpleNamespace(status_code=200, text="", json=lambda: {
        "response": json.dumps(output), "done_reason": done_reason, "done": True
    })
    monkeypatch.setattr(vision.requests, "get", lambda *a, **kw: tag_response)
    monkeypatch.setattr(vision.requests, "post", lambda *a, **kw: model_response)
    monkeypatch.setattr(vision.gpu_coordinator, "acquire_for_inference", lambda **kw: nullcontext())
    monkeypatch.setattr(vision.gpu_coordinator, "check_inference_allowed", lambda: (True, ""))


def image_request(client):
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=100, height=100)
    page.insert_text((10, 30), "Timetable")
    data = page.get_pixmap().tobytes("png")
    doc.close()
    return client.post("/api/timetable/extract", json={
        "filename": "fixture.png", "image_base64": base64.b64encode(data).decode()
    })


def test_missing_image_fields_stay_unknown_in_draft(client, monkeypatch):
    fake_vision(monkeypatch, {"entries": [{"course": "Math", "weekday": None,
               "start_time": None, "end_time": None, "period": "1-3", "room": None}],
               "uncertainties": ["Ngày không rõ"]})
    response = image_request(client)
    assert response.status_code == 200, response.text
    entry = response.json()["entries"][0]
    assert entry["weekday"] is None
    assert entry["start_time"] is None and entry["end_time"] is None
    assert client.get("/api/timetable").json()["entries"] == []


@pytest.mark.parametrize("output", [
    {"entries": "a timetable", "uncertainties": []},
    {"entries": [{"course": "Math"}, "unparsed second course"], "uncertainties": []},
    {"entries": [], "uncertainties": "the picture is blurry"},
])
def test_malformed_output_is_not_silently_shortened(client, monkeypatch, output):
    fake_vision(monkeypatch, output)
    response = image_request(client)
    assert response.status_code == 422, response.text


def test_truncated_model_output_cannot_be_cached_as_complete(client, monkeypatch):
    fake_vision(monkeypatch, {"entries": [{"course": "Math", "weekday": 1,
               "start_time": "08:00", "end_time": "09:00"}], "uncertainties": []},
               done_reason="length")
    response = image_request(client)
    assert response.status_code == 422, response.text
    from app import timetable_store
    with timetable_store.get_connection() as conn:
        assert conn.execute("select count(*) from timetable_vlm_cache").fetchone()[0] == 0


def test_missing_digest_is_unavailable_instead_of_hardcoded_provenance(client, monkeypatch):
    fake_vision(monkeypatch, {"entries": [], "uncertainties": []}, digest=None)
    response = image_request(client)
    assert response.status_code == 503, response.text


def test_copied_day_label_controls_iso_day(client, monkeypatch):
    fake_vision(monkeypatch, {"entries": [{"course": "Math", "weekday_label": "Thứ 4", "weekday": 4,
                "start_time": "08:00", "end_time": "09:00"}], "uncertainties": []})
    response = image_request(client)
    assert response.status_code == 200, response.text
    assert response.json()["entries"][0]["weekday"] == 3


def test_unlabelled_model_integer_is_not_trusted_as_day(client, monkeypatch):
    fake_vision(monkeypatch, {"entries": [{"course": "Math", "weekday": 2,
                "start_time": "08:00", "end_time": "09:00"}], "uncertainties": []})
    response = image_request(client)
    assert response.status_code == 200, response.text
    assert response.json()["entries"][0]["weekday"] is None


def test_draft_provenance_survives_reload(client, monkeypatch):
    from app import timetable_vision as vision
    fake_vision(monkeypatch, {"entries": [{"course": "Math", "weekday_label": "Monday",
                "start_time": "08:00", "end_time": "09:00"}], "uncertainties": []})
    response = image_request(client)
    assert response.status_code == 200, response.text
    result = response.json()
    draft = client.get("/api/timetable/drafts/" + result["draft_id"]).json()
    assert draft["model_digest"] == "d" * 64
    assert draft["prompt_version"] == vision.PROMPT_VERSION
    assert draft["options"]["temperature"] == 0
    assert draft["raw_model_output"]
    assert client.get("/api/timetable/images/" + result["image_hash"]).status_code == 200


@pytest.mark.parametrize("bad_course", [["Math"], {"name": "Math"}, True])
def test_model_course_type_is_checked(client, monkeypatch, bad_course):
    fake_vision(monkeypatch, {"entries": [{"course": bad_course, "weekday_label": "Monday"}],
                            "uncertainties": []})
    response = image_request(client)
    assert response.status_code == 422, response.text

@pytest.mark.parametrize("field,value", [
    ("weekday_label", True), ("start_time", ["08:00"]),
    ("room", {"code": "A101"}), ("period", [1, 3]),
])
def test_other_model_fields_have_nullable_string_types(client, monkeypatch, field, value):
    entry = {"course": "Math", "weekday_label": "Monday", "start_time": "08:00", "end_time": "09:00"}
    entry[field] = value
    fake_vision(monkeypatch, {"entries": [entry], "uncertainties": []})
    assert image_request(client).status_code == 422


def test_large_image_is_bounded_for_inference_and_uses_schema(client, monkeypatch):
    import io
    from PIL import Image
    from app import timetable_vision as vision
    fake_vision(monkeypatch, {"entries": [], "uncertainties": []})
    post = vision.requests.post
    seen = []
    def capture(*args, **kwargs):
        seen.append(kwargs["json"])
        return post(*args, **kwargs)
    monkeypatch.setattr(vision.requests, "post", capture)
    buf = io.BytesIO()
    Image.new("RGB", (3000, 1000), "white").save(buf, "PNG")
    response = client.post("/api/timetable/extract", json={"filename": "large.png", "image_base64": base64.b64encode(buf.getvalue()).decode()})
    assert response.status_code == 200, response.text
    assert isinstance(seen[0]["format"], dict)
    with Image.open(io.BytesIO(base64.b64decode(seen[0]["images"][0]))) as sent:
        assert max(sent.size) <= 1600
    with Image.open(io.BytesIO(client.get("/api/timetable/images/"+response.json()["image_hash"]).content)) as original:
        assert original.size == (3000, 1000)


def test_confirmation_preserves_original_and_reviewed_edits(client, monkeypatch):
    fake_vision(monkeypatch, {"entries": [{"course": "Read from image", "weekday_label": "Monday", "start_time": "08:00", "end_time": "09:00"}], "uncertainties": []})
    result = image_request(client).json()
    reviewed = [{"course": "Corrected course", "weekday": 1, "start_time": "08:00", "end_time": "09:00"}]
    response = client.post("/api/timetable/confirm", json={"draft_id":result["draft_id"],"entries":reviewed})
    assert response.status_code == 200, response.text
    stored = client.get("/api/timetable/drafts/"+result["draft_id"]).json()
    assert stored["entries"][0]["course"] == "Read from image"
    assert stored["confirmed_at"]
    assert stored["confirmed_entries"][0]["course"] == "Corrected course"
