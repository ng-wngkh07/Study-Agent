import hashlib
import json

import pymupdf
import pytest

from app.indexer import KnowledgeIndexer
from app.pdf_extractor import PDFExtractor
from app.training_data import is_chunk_allowed_in_training


def make_source(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    doc.new_page()
    doc.save(path)
    doc.close()


def test_review_updates_exact_nested_document_and_keeps_other_approved_chunks(tmp_path, monkeypatch):
    root = tmp_path / "src"
    indexer = KnowledgeIndexer(tmp_path / "index.db", root)
    for name in ("lesson.pdf", "nested/lesson.pdf"):
        p = root / name
        make_source(p)
        result = PDFExtractor.extract_pdf(p, rel_path=name)
        indexer._save_document_record(result, "scanned_unocred", True)
    old = "Previously approved page text must survive another document's correction."
    with indexer.get_connection() as conn:
        ids = {r["filename"]: r["id"] for r in conn.execute("SELECT id,filename FROM documents")}
    indexer._save_chunks(ids["lesson.pdf"], [{"book_title": "Root", "filename": "lesson.pdf", "page_num": 1, "chunk_index": 0, "text": old}])
    monkeypatch.setattr(indexer.ollama, "check_health", lambda: False)
    corrected = "Nội dung đã đối chiếu của tài liệu nằm trong thư mục con."
    result = indexer.update_page_chunks("nested/lesson.pdf", 1, corrected)
    assert result["status"] == "success"
    with indexer.get_connection() as conn:
        assert conn.execute("SELECT text FROM chunks WHERE doc_id=?", (ids["lesson.pdf"],)).fetchone()[0] == old
        assert conn.execute("SELECT text FROM chunks WHERE doc_id=?", (ids["nested/lesson.pdf"],)).fetchone()[0] == corrected


def test_unverified_ocr_revision_does_not_hide_matching_approved_transcript(tmp_path, monkeypatch):
    src = tmp_path / "notes.pdf"
    make_source(src)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    cache = tmp_path / "cache"
    cache.mkdir()
    text = "Đây là bản chép đã được đối chiếu với trang viết tay."
    good = {"source_hash": digest, "page_num": 1, "text": text,
            "is_verified": True, "verified_by": "Reviewer", "verified_at": "2026-10-04"}
    bad = dict(good, text="Bản OCR mới còn sai và chưa được đối chiếu.", is_verified=False)
    (cache / ("0" * 64 + ".json")).write_text(json.dumps(good))
    (cache / ("f" * 64 + ".json")).write_text(json.dumps(bad))
    class OrderedCache:
        def glob(self, _):
            return [cache / ("0" * 64 + ".json"), cache / ("f" * 64 + ".json")]
    monkeypatch.setattr("app.vision_ocr.CACHE_DIR", OrderedCache())
    doc = {"filename": src.name, "filepath": str(src), "file_hash": digest, "is_scanned": True}
    assert is_chunk_allowed_in_training(doc, 1, text) is True
    assert is_chunk_allowed_in_training(doc, 1, text + " Ý ngoài bản chép.") is False


def test_failed_chunk_revision_keeps_previous_approved_page(tmp_path, monkeypatch):
    src = tmp_path / "src/notes.pdf"
    make_source(src)
    indexer = KnowledgeIndexer(tmp_path / "index.db", src.parent)
    doc_id = indexer._save_document_record(PDFExtractor.extract_pdf(src), "indexed", True, 1)
    old = "Previously approved page remains readable if a correction cannot be indexed."
    indexer._save_chunks(doc_id, [{"book_title": "Notes", "filename": src.name, "page_num": 1, "chunk_index": 0, "text": old}])
    def fail(*args, **kwargs):
        raise ValueError("Could not prepare corrected chunks")
    monkeypatch.setattr("app.chunker.TextChunker.chunk_page", fail)
    monkeypatch.setattr(indexer.ollama, "check_health", lambda: False)
    with pytest.raises((ValueError, AttributeError)):
        indexer.update_page_chunks(src.name, 1, "Reviewed correction")
    with indexer.get_connection() as conn:
        assert conn.execute("SELECT text FROM chunks WHERE doc_id=?", (doc_id,)).fetchone()[0] == old
