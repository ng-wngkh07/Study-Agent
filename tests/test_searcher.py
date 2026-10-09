import pytest
import sqlite3
from pathlib import Path
from app.config import DB_PATH, SRC_DIR
from app.searcher import HybridSearcher
from app.indexer import KnowledgeIndexer

def test_database_is_populated():
    indexer = KnowledgeIndexer()
    status = indexer.get_status()
    assert status["total_documents"] >= 33
    assert status["total_indexed_pages"] > 5000
    assert status["total_chunks"] > 10000

def test_fts5_search():
    searcher = HybridSearcher()
    # Search for a well-known concept in psychology
    results = searcher.search_fts("Hệ thống 1 và Hệ thống 2", limit=5)
    assert len(results) > 0
    first = results[0]
    assert "text" in first
    assert "page_num" in first
    assert "book_title" in first
    assert first["page_num"] > 0


def test_numbered_concepts_stay_together_in_retrieval():
    searcher = HybridSearcher()
    question = "Hệ thống 1 và Hệ thống 2 khác nhau thế nào?"
    results = searcher.search_hybrid(question, top_k=8, embed_model=None)
    assert any("tu-duy-nhanh-va-cham" in item["filename"] for item in results[:3])
    assert any("Hệ thống 1" in item["text"] and "Hệ thống 2" in item["text"] for item in results)

def test_hybrid_search_results_structure():
    searcher = HybridSearcher()
    results = searcher.search_hybrid("sang chấn tâm lý ảnh hưởng cơ thể", top_k=4, embed_model=None)
    assert len(results) > 0
    assert len(results) <= 4
    for r in results:
        assert "citation_label" in r
        assert "Trang" in r["citation_label"]
        assert "safe_text" in r


def test_duplicate_pdf_aliases_do_not_displace_distinct_evidence(tmp_path, monkeypatch):
    searcher = HybridSearcher(tmp_path / "unused.db")
    rows = [{"chunk_id": i, "filename": name, "book_title": name,
             "page_num": 1, "chunk_index": 0, "text": text, "fts_rank": i}
            for i, name, text in [
                (1, "book.pdf", "Trí nhớ lưu giữ thông tin trong cuộc sống."),
                (2, "book (1).pdf", "Trí nhớ  lưu giữ thông tin trong cuộc sống."),
                (3, "other.pdf", "Khả năng nhớ lại chịu ảnh hưởng của bối cảnh học tập."),
            ]]
    monkeypatch.setattr(searcher, "search_fts", lambda *_args, **_kwargs: rows)
    result = searcher.search_hybrid("trí nhớ", top_k=2, embed_model=None)
    assert [r["chunk_id"] for r in result] == [1, 3]
