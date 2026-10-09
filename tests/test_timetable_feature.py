"""Comprehensive tests for Timetable Feature (S01-S03)."""

import base64
import os
import pymupdf
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app import server, timetable_store, timetable_vision, timetable_ics


@pytest.fixture
def isolated_client(tmp_path, monkeypatch):
    db_path = tmp_path / "test_timetable.db"
    monkeypatch.setenv("TIMETABLE_DB_PATH", str(db_path))
    return TestClient(server.app)


def make_test_png_bytes(width=100, height=100) -> bytes:
    """Create a minimal valid PNG image in memory using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page(width=width, height=height)
    page.draw_rect(pymupdf.Rect(10, 10, 90, 90), color=(0, 0, 1), fill=(0.9, 0.9, 0.9))
    page.insert_text((15, 30), "THỜI KHÓA BIỂU", fontsize=10)
    page.insert_text((15, 50), "Toán rời rạc - Thứ 2 - 08:00 - 10:00", fontsize=8)
    pix = page.get_pixmap()
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


def test_image_validation_bounds():
    # 1. Invalid base64
    with pytest.raises(ValueError):
        timetable_vision.validate_image_payload("test.png", "not-base-64!!!")

    # 2. Valid image
    png_bytes = make_test_png_bytes()
    b64 = base64.b64encode(png_bytes).decode()
    raw_bytes, sha = timetable_vision.validate_image_payload("test.png", b64)
    assert len(raw_bytes) == len(png_bytes)
    assert len(sha) == 64


def test_timetable_crud_and_isolation(isolated_client):
    # 1. Initially empty
    res = isolated_client.get("/api/timetable")
    assert res.status_code == 200
    assert res.json()["entries"] == []

    # 2. Add manual entry
    res = isolated_client.post("/api/timetable/manual", json={
        "course": "Đại số tuyến tính",
        "weekday": 2,
        "start_time": "07:30",
        "end_time": "09:30",
        "room": "B1-204"
    })
    assert res.status_code == 200
    entry_id = res.json()["id"]

    # 3. Verify retrieved
    res = isolated_client.get("/api/timetable")
    entries = res.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["course"] == "Đại số tuyến tính"
    assert entries[0]["weekday"] == 2
    assert entries[0]["room"] == "B1-204"

    # 4. Delete entry
    res = isolated_client.delete(f"/api/timetable/entries/{entry_id}")
    assert res.status_code == 200
    assert isolated_client.get("/api/timetable").json()["entries"] == []


def test_draft_confirmation_workflow(isolated_client):
    draft_id = "draft_test_123"
    entries = [
        {"course": "Lập trình C++", "weekday": 1, "start_time": "08:00", "end_time": "11:15", "room": "A201"},
        {"course": "Tâm lý học đại cương", "weekday": 4, "start_time": "13:30", "end_time": "16:00", "room": "C105"}
    ]
    timetable_store.save_draft(
        draft_id=draft_id,
        image_hash="hash123",
        filename="tkb.png",
        entries=entries,
        uncertainties=["Kiểm tra lại phòng học"]
    )

    # Fetch draft
    draft_res = isolated_client.get(f"/api/timetable/drafts/{draft_id}")
    assert draft_res.status_code == 200
    assert len(draft_res.json()["entries"]) == 2

    # Confirm draft
    confirm_res = isolated_client.post("/api/timetable/confirm", json={
        "draft_id": draft_id,
        "entries": entries
    })
    assert confirm_res.status_code == 200
    assert confirm_res.json()["saved_entries"] == 2

    # Confirmed timetable has entries
    tt_res = isolated_client.get("/api/timetable")
    assert len(tt_res.json()["entries"]) == 2


def test_conflict_detection():
    entries = [
        {"course": "Vật lý đại cương", "weekday": 2, "start_time": "08:00", "end_time": "10:00"},
        {"course": "Giải tích 1", "weekday": 2, "start_time": "09:30", "end_time": "11:30"},
        {"course": "Triết học", "weekday": 3, "start_time": "08:00", "end_time": "10:00"},
    ]
    conflicts = timetable_vision.detect_conflicts(entries)
    assert len(conflicts) == 1
    assert "Vật lý đại cương" in conflicts[0] and "Giải tích 1" in conflicts[0]


def test_ics_export_generation(isolated_client):
    entries = [
        {"course": "Toán rời rạc", "weekday": 1, "start_time": "08:00", "end_time": "10:00", "room": "A301"},
        {"course": "Cơ sở dữ liệu", "weekday": 5, "start_time": "13:30", "end_time": "15:30", "room": "B202"}
    ]
    ics_text = timetable_ics.generate_ics(entries, "2026-10-05", "2026-12-31")
    assert "BEGIN:VCALENDAR" in ics_text
    assert "END:VCALENDAR" in ics_text
    assert "TZID:Asia/Ho_Chi_Minh" in ics_text
    assert "SUMMARY:Toán rời rạc" in ics_text
    assert "SUMMARY:Cơ sở dữ liệu" in ics_text
    assert "BYDAY=MO" in ics_text
    assert "BYDAY=FR" in ics_text

    # Via HTTP
    for e in entries:
        isolated_client.post("/api/timetable/manual", json=e)

    res = isolated_client.get("/api/timetable/export.ics?start_date=2026-10-05&end_date=2026-12-31")
    assert res.status_code == 200
    assert "text/calendar" in res.headers["content-type"]
    assert "ATTACHMENT" in res.headers["content-disposition"].upper()
    assert "SUMMARY:Toán rời rạc" in res.text
