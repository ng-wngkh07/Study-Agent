import hashlib
import json
import sqlite3

import pytest

from app.bilingual_terms import translation_is_plausible, translation_guidance
from app.prepare_v5 import book_partition, plan, prepare


def test_holdout_excludes_all_identical_pdf_aliases():
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE documents(filename TEXT,file_hash TEXT,status TEXT)")
        db.executemany("INSERT INTO documents VALUES(?,?,'indexed')", [
            ("holdout.pdf", "same"), ("renamed-holdout.pdf", "same"),
            ("train.pdf", "other"), ("train (1).pdf", "other"),
        ])
        allowed, heldout = book_partition(db, {"holdout.pdf"})
        assert heldout == {"holdout.pdf", "renamed-holdout.pdf"}
        assert allowed == {"train.pdf"}


def test_expansion_cannot_reuse_an_unapproved_dataset(tmp_path):
    previous = tmp_path / "v4"
    previous.mkdir()
    (previous/"train.jsonl").write_text("changed\n")
    (previous/"valid.jsonl").write_text("valid\n")
    (previous/"approval.json").write_text(json.dumps({"dataset_sha256": "outdated"}))
    with pytest.raises(ValueError, match="Hash"):
        plan(previous, tmp_path/"v5")
    assert not (tmp_path/"v5").exists()


def test_expansion_rejects_sources_that_do_not_match_index(tmp_path):
    previous = tmp_path/"v4"
    previous.mkdir()
    train = b"train\n"
    valid = b"valid\n"
    (previous/"train.jsonl").write_bytes(train)
    (previous/"valid.jsonl").write_bytes(valid)
    (previous/"approval.json").write_text(json.dumps({"dataset_sha256": hashlib.sha256(train+valid).hexdigest()}))
    (previous/"summary.json").write_text(json.dumps({"held_out_books": []}))
    record = {"key": "old", "language": "vi", "pair": {"filename": "train.pdf", "sources": [{"id": "S1", "page": 1, "text": "Nội dung không khớp."}]}, "items": []}
    (previous/"approved_manifest.jsonl").write_text(json.dumps(record)+"\n")
    db_path = tmp_path/"index.db"
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE documents(filename TEXT,file_hash TEXT,status TEXT)")
        db.execute("INSERT INTO documents VALUES('train.pdf','hash','indexed')")
        db.execute("CREATE TABLE chunks(filename TEXT,page_num INTEGER,text TEXT)")
        db.execute("INSERT INTO chunks VALUES('train.pdf',1,'Đoạn đúng trong chỉ mục.')")
    with pytest.raises(ValueError, match="đối chiếu"):
        plan(previous, tmp_path/"v5", db_path=db_path)


def test_runtime_translation_rejects_wrong_language_even_when_long_enough():
    source = "The mind and body respond to trauma, and the nervous system changes with experience."
    assert not translation_is_plausible(source, "这是关于人类记忆与心理学的说明。"*8)
    assert not translation_is_plausible(source, source*2)
    assert translation_is_plausible(source, "Tâm trí và cơ thể phản ứng với sang chấn, hệ thần kinh thay đổi qua trải nghiệm.")


def test_translation_glossary_respects_the_context_of_shadowing():
    guidance = translation_guidance("The shadowed ear receives the message in this attention experiment.")
    assert "nghe và lặp lại" in guidance
    assert "khía cạnh bị che giấu" not in guidance
    assert "gene =" not in guidance
    assert "hồi hải mã" in translation_guidance("Another job of the hippocampus is to project information to cortical regions.")
    assert "truyền/chuyển thông tin" in translation_guidance("The hippocampus will project information to cortical regions.")


def test_generation_resume_skips_saved_sources_and_records_actual_teacher(tmp_path):
    pair = {"filename": "book.pdf", "title": "Sách", "sources": [
        {"id": "S1", "page": 1, "text": "Trí nhớ giúp con người lưu giữ thông tin trong cuộc sống."},
        {"id": "S2", "page": 2, "text": "Trí nhớ có thể thay đổi và việc nhớ lại có thể sai lệch."},
    ]}
    (tmp_path/"plan.json").write_text(json.dumps({"pairs": [pair]}))
    calls = []

    def teacher(actual_pair, **kwargs):
        calls.append(actual_pair)
        return {"language": "vi", "translations": {}, "items": [{
            "question": "Hai đoạn cho biết gì về vai trò và giới hạn của trí nhớ?",
            "answer": "Trí nhớ lưu giữ thông tin, nhưng điều được nhớ lại vẫn có thể thay đổi hoặc sai lệch. [S1] [S2]",
        }]}

    prepare(tmp_path, teacher="mlx-qwen2.5-3b-base", teacher_fn=teacher)
    prepare(tmp_path, teacher="mlx-qwen2.5-3b-base", teacher_fn=teacher)
    records = [json.loads(line) for line in (tmp_path/"manifest.jsonl").read_text().splitlines()]
    assert len(calls) == len(records) == 1
    assert records[0]["translation_model"] == "mlx-qwen2.5-3b-base"
    assert records[0]["pair"] == pair
