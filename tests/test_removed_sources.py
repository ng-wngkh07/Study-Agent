from app.indexer import KnowledgeIndexer


def test_removed_pdf_is_removed_from_search_index(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    indexer = KnowledgeIndexer(db_path=tmp_path / "knowledge.db", src_dir=src)
    with indexer.get_connection() as conn:
        doc_id = conn.execute(
            """INSERT INTO documents
            (filename, clean_title, filepath, file_size, file_hash, total_pages,
             extracted_pages_count, is_scanned, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("removed.pdf", "Removed", str(src / "removed.pdf"), 1, "hash", 1, 1, 0, "indexed"),
        ).lastrowid
        conn.execute(
            """INSERT INTO chunks (doc_id, book_title, filename, page_num, chunk_index, text)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (doc_id, "Removed", "removed.pdf", 1, 0, "unique_phrase_for_removed_book"),
        )

    report = indexer.index_all(embed_model=None)

    assert report["removed_files"] == 1
    with indexer.get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH ?",
            ("unique_phrase_for_removed_book",),
        ).fetchone()[0] == 0
