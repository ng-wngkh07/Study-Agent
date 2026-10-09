"""Clean team demo builds without books/models and leaves canonical data alone."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_clean_demo_fts_source_and_api(tmp_path):
    for folder in ("app", "static", "tests/fixtures"):
        shutil.copytree(ROOT / folder, tmp_path / folder,
                        ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/dev.py", tmp_path / "scripts/dev.py")
    (tmp_path / "data").mkdir()
    sentinel = tmp_path / "data/knowledge_base.db"
    sentinel.write_bytes(b"DO NOT TOUCH COORDINATOR DATA")
    result = subprocess.run([sys.executable, "scripts/dev.py", "demo"], cwd=tmp_path,
        capture_output=True, text=True, encoding="utf-8", timeout=30,
        env={**os.environ, "PYTHONUTF8": "1"})
    assert result.returncode == 0, result.stderr
    assert sentinel.read_bytes() == b"DO NOT TOUCH COORDINATOR DATA"
    assert (tmp_path / "data/team-demo/knowledge_base.db").exists()
    code = '''
from scripts.dev import configure
configure("demo")
from fastapi.testclient import TestClient
from app.server import app
client = TestClient(app)
assert client.get("/").status_code == 200
rows = client.get("/api/documents/search", params={"q":"trí nhớ"}).json()["results"]
assert rows and any("thời gian ngắn" in row["text"] for row in rows)
assert client.get("/api/timetable").status_code == 200
print("demo API OK")
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path,
        capture_output=True, text=True, encoding="utf-8", timeout=30,
        env={**os.environ, "PYTHONUTF8": "1"})
    assert result.returncode == 0, result.stderr


def test_synthetic_table_preserves_unresolved_and_invalid_cells():
    from app.timetable_table import parse_registered_table
    # Coordinates are normalized Apple Vision style (bottom-left origin),
    # allowing the parser to be tested independently of an OCR installation.
    lines = [
        {"text":"Ten MH", "bounds":[.25,.90,.08,.02]},
        {"text":"Lich LT", "bounds":[.50,.90,.08,.02]},
        {"text":"Lich TH", "bounds":[.75,.90,.08,.02]},
        {"text":"DEMO101", "bounds":[.03,.70,.08,.02]},
        {"text":"Demo course", "bounds":[.25,.70,.08,.02]},
        {"text":"T2 09:00-10:00 (A101)", "bounds":[.49,.70,.10,.02]},
    ]
    record = parse_registered_table(lines)
    assert record["entries"][0]["weekday"] == 1
    assert record["entries"][0]["start_time"] == "09:00"
    lines[-1]["text"] = "T2 29:00-30:00 (A101)"
    record = parse_registered_table(lines)
    assert record["entries"][0]["start_time"] is None
    assert record["uncertainties"]


def test_demo_fixture_contract():
    from PIL import Image
    import fitz
    with fitz.open(ROOT / "tests/fixtures/documents/demo.pdf") as doc:
        assert doc.page_count == 1
        assert "working memory" in doc[0].get_text().lower()
    with Image.open(ROOT / "tests/fixtures/timetables/demo.png") as image:
        assert image.width >= 600 and image.height >= 200
    expected = json.loads((ROOT / "tests/fixtures/timetables/expected.json").read_text(encoding="utf-8"))
    assert expected["entries"][0]["weekday"] == 1
