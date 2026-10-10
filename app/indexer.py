import os
import json
import sqlite3
import struct
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from app.config import (
    SRC_DIR, DB_PATH, DEFAULT_EMBED_MODEL,
    CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS
)
from app.pdf_extractor import PDFExtractor, PDFExtractionResult
from app.chunker import TextChunker
from app.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

def pack_vector(vec: List[float]) -> bytes:
    """Pack float list into binary bytes."""
    return struct.pack(f"{len(vec)}f", *vec)

def unpack_vector(blob: bytes) -> np.ndarray:
    """Unpack binary bytes into numpy float32 array."""
    count = len(blob) // 4
    return np.array(struct.unpack(f"{count}f", blob), dtype=np.float32)

class KnowledgeIndexer:
    def __init__(self, db_path: Path = DB_PATH, src_dir: Path = SRC_DIR):
        self.db_path = db_path
        self.src_dir = src_dir
        self.ollama = OllamaClient()
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Create database tables and FTS5 virtual table."""
        with self.get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                clean_title TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                total_pages INTEGER NOT NULL,
                extracted_pages_count INTEGER NOT NULL,
                is_scanned INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                book_title TEXT NOT NULL,
                filename TEXT NOT NULL,
                page_num INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
            CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(doc_id, page_num);

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                book_title,
                text,
                content='chunks',
                content_rowid='id',
                tokenize='unicode61 remove_diacritics 0'
            );

            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, book_title, text) VALUES (new.id, new.book_title, new.text);
            END;

            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, book_title, text) VALUES('delete', old.id, old.book_title, old.text);
            END;

            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, book_title, text) VALUES('delete', old.id, old.book_title, old.text);
                INSERT INTO chunks_fts(rowid, book_title, text) VALUES (new.id, new.book_title, new.text);
            END;
            """)

    def get_indexed_files_map(self) -> Dict[str, Dict[str, Any]]:
        """Return dict of {filename: {file_hash, filepath, status, id, ...}}"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id, filename, filepath, file_hash, status, total_pages, is_scanned FROM documents")
            return {row["filename"]: dict(row) for row in cursor.fetchall()}

    def backfill_missing_embeddings(
        self,
        embed_model: str = DEFAULT_EMBED_MODEL,
        batch_size: int = 32,
        limit: int = 0,
        progress_callback: Optional[callable] = None
    ) -> int:
        """
        Populate embeddings for all chunks that currently have embedding IS NULL.
        Allows adding vector search capability to already indexed files.
        """
        # Find actual model name from Ollama (e.g. match bge-m3 or bge-m3:latest)
        resolved_model = self.ollama.find_best_embed_model(embed_model) or embed_model
        test_emb = self.ollama.get_embedding("test", model=resolved_model)
        if test_emb is None:
            logger.info(f"Mô hình embedding '{resolved_model}' chưa khả dụng trong Ollama để bổ sung embedding.")
            return 0

        with self.get_connection() as conn:
            if limit > 0:
                missing_chunks = conn.execute(
                    "SELECT id, text FROM chunks WHERE embedding IS NULL ORDER BY id LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                missing_chunks = conn.execute(
                    "SELECT id, text FROM chunks WHERE embedding IS NULL ORDER BY id"
                ).fetchall()

        total_missing = len(missing_chunks)
        if total_missing == 0:
            return 0

        logger.info(f"Bắt đầu bổ sung embedding cho {total_missing} đoạn chỉ mục bằng mô hình '{resolved_model}'...")
        count = 0

        with self.get_connection() as conn:
            for start in range(0, total_missing, batch_size):
                batch = missing_chunks[start:start + batch_size]
                vectors = self.ollama.get_batch_embeddings(
                    [row["text"] for row in batch], model=resolved_model
                )
                for row, vec in zip(batch, vectors):
                    if vec:
                        conn.execute(
                            "UPDATE chunks SET embedding = ? WHERE id = ?",
                            (pack_vector(vec), row["id"]),
                        )
                        count += 1
                conn.commit()
                if progress_callback:
                    done = min(start + len(batch), total_missing)
                    progress_callback(done, total_missing, f"Đã bổ sung {count}/{total_missing} vector embedding...")

        return count

    def index_all(
        self,
        force: bool = False,
        ocr: bool = False,
        embed_model: Optional[str] = DEFAULT_EMBED_MODEL,
        progress_callback: Optional[callable] = None,
        force_ocr_files: Optional[set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Index all PDFs from SRC_DIR.
        Supports incremental updates (skips unchanged files unless force=True).
        Automatically backfills vector embeddings if embed_model is available.
        """
        report = {
            "total_files": 0,
            "indexed_files": 0,
            "skipped_files": 0,
            "removed_files": 0,
            "scanned_files": [],
            "error_files": [],
            "total_pages_indexed": 0,
            "total_chunks_created": 0,
            "embeddings_backfilled": 0,
            "embedding_enabled": False,
            "details": []
        }

        if not self.src_dir.exists():
            report["error"] = f"Thư mục nguồn {self.src_dir} không tồn tại."
            return report

        discovery = PDFExtractor.discover_source_files(self.src_dir)
        source_files = discovery["supported"]
        report["total_files"] = len(source_files)
        report["unsupported_files"] = discovery.get("unsupported", [])
        report["symlink_violations"] = discovery.get("symlink_violations", [])

        # Check if embedding model is functional
        resolved_embed_model = self.ollama.find_best_embed_model(embed_model) if embed_model else None
        can_embed = False
        if resolved_embed_model:
            test_emb = self.ollama.get_embedding("test", model=resolved_embed_model)
            if test_emb is not None:
                can_embed = True
                report["embedding_enabled"] = True
                logger.info(f"Đã kích hoạt mô hình embedding Ollama: {resolved_embed_model}")
            else:
                logger.info(f"Mô hình embedding '{resolved_embed_model}' chưa khả dụng trong Ollama.")

        indexed_map = self.get_indexed_files_map()
        force_ocr_files = force_ocr_files or set()
        current_keys = {str(p.relative_to(self.src_dir)) for p in source_files}

        obsolete_filenames = set(indexed_map) - current_keys
        if obsolete_filenames:
            with self.get_connection() as conn:
                conn.executemany(
                    "DELETE FROM documents WHERE filename = ?",
                    [(name,) for name in obsolete_filenames],
                )
            report["removed_files"] = len(obsolete_filenames)

        for idx, file_path in enumerate(source_files, 1):
            rel_path = str(file_path.relative_to(self.src_dir))
            file_hash = PDFExtractor.calculate_file_hash(file_path)
            current_abs_path = str(file_path.resolve())

            if progress_callback:
                progress_callback(idx, len(source_files), rel_path, "Đang xử lý...")

            # Check for incremental skip
            # The document identity is strictly its relative path within src_dir.
            # Never fallback match_key to basename for nested files.
            if not force and rel_path in indexed_map:
                existing = indexed_map[rel_path]
                if existing["file_hash"] == file_hash and existing["status"] in ("indexed", "scanned_unocred", "ocr_partial_reviewed") and rel_path not in force_ocr_files and not (ocr and existing["status"] == "scanned_unocred"):
                    # If project directory moved or filepath is stale, rebase filepath to current resolved path
                    if existing.get("filepath") != current_abs_path:
                        with self.get_connection() as conn:
                            conn.execute(
                                "UPDATE documents SET filepath = ? WHERE id = ?",
                                (current_abs_path, existing["id"]),
                            )
                        existing["filepath"] = current_abs_path

                    report["skipped_files"] += 1
                    report["details"].append({
                        "filename": rel_path,
                        "status": "skipped",
                        "reason": "File không thay đổi (đã lập chỉ mục, cập nhật đường dẫn)"
                    })
                    if existing["is_scanned"]:
                        report["scanned_files"].append(rel_path)
                    continue

            # Extract text
            is_force = (rel_path in force_ocr_files)
            extract_res = PDFExtractor.extract_file(file_path, force_ocr=is_force) if is_force else PDFExtractor.extract_file(file_path)
            if ocr and extract_res.is_scanned and not is_force:
                extract_res = PDFExtractor.extract_file(file_path, ocr=True)

            extract_res.filename = rel_path

            if extract_res.error_message:
                report["error_files"].append({"filename": rel_path, "error": extract_res.error_message})
                # Extraction failures must not erase a previously usable index
                # or advance its hash; the next scan must be able to retry.
                if rel_path not in indexed_map:
                    self._save_document_record(extract_res, status="error", is_scanned=False)
                report["details"].append({
                    "filename": rel_path,
                    "status": "error",
                    "error": extract_res.error_message
                })
                continue

            if extract_res.is_scanned:
                report["scanned_files"].append(rel_path)
                self._save_document_record(extract_res, status="scanned_unocred", is_scanned=True)
                report["details"].append({
                    "filename": rel_path,
                    "status": "scanned_unocred",
                    "total_pages": extract_res.total_pages,
                    "warning": "Tài liệu dạng scan/ảnh (không có lớp chữ số OCR)"
                })
                continue

            # Chunk and Index pages
            all_chunks = []
            extracted_pages_count = 0
            for page in extract_res.extracted_pages:
                if page.get("has_text") and page.get("text"):
                    extracted_pages_count += 1
                    chunks = TextChunker.chunk_page(
                        book_title=extract_res.clean_title,
                        filename=rel_path,
                        page_num=page["page_num"],
                        page_text=page["text"]
                    )
                    all_chunks.extend(chunks)

            # Prepare embeddings before touching the active document. Replace the
            # metadata, chunks and trigger-maintained FTS in one transaction.
            prepared = self._prepare_chunk_rows(all_chunks, can_embed, resolved_embed_model)
            with self.get_connection() as conn:
                doc_id = self._save_document_record(
                    extract_res, status="indexed", is_scanned=False,
                    extracted_pages_count=extracted_pages_count, connection=conn,
                )
                chunks_inserted = self._insert_chunk_rows(conn, doc_id, prepared)

            report["indexed_files"] += 1
            report["total_pages_indexed"] += extracted_pages_count
            report["total_chunks_created"] += chunks_inserted
            report["details"].append({
                "filename": rel_path,
                "clean_title": extract_res.clean_title,
                "status": "indexed",
                "total_pages": extract_res.total_pages,
                "extracted_pages": extracted_pages_count,
                "chunks_count": chunks_inserted,
                "failed_pages": extract_res.failed_pages,
                "ocr_pages": extract_res.ocr_pages,
            })

        # If embedding is now enabled, backfill any chunks from previously indexed files that have NULL embeddings
        if can_embed and resolved_embed_model:
            backfilled = self.backfill_missing_embeddings(
                embed_model=resolved_embed_model,
                progress_callback=lambda cur, tot, msg: progress_callback(len(source_files), len(source_files), "Embedding Backfill", msg) if progress_callback else None
            )
            report["embeddings_backfilled"] = backfilled

        return report

    def _save_document_record(
        self,
        res: PDFExtractionResult,
        status: str,
        is_scanned: bool,
        extracted_pages_count: int = 0,
        *,
        connection: Optional[sqlite3.Connection] = None
    ) -> int:
        """Upsert document record in DB and delete old chunks if re-indexing."""
        if connection is None:
            with self.get_connection() as conn:
                return self._save_document_record(
                    res, status, is_scanned, extracted_pages_count, connection=conn,
                )
        conn = connection
        # Check existing
        row = conn.execute("SELECT id FROM documents WHERE filename = ?", (res.filename,)).fetchone()
        if row:
            doc_id = row["id"]
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            conn.execute("""
            UPDATE documents SET
                clean_title = ?,
                filepath = ?,
                file_size = ?,
                file_hash = ?,
                total_pages = ?,
                extracted_pages_count = ?,
                is_scanned = ?,
                status = ?,
                error_message = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (
                res.clean_title, str(res.filepath), res.file_size_bytes,
                res.file_hash, res.total_pages, extracted_pages_count,
                1 if is_scanned else 0, status, res.error_message, doc_id
            ))
        else:
            cursor = conn.execute("""
            INSERT INTO documents (
                filename, clean_title, filepath, file_size, file_hash,
                total_pages, extracted_pages_count, is_scanned, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                res.filename, res.clean_title, str(res.filepath), res.file_size_bytes,
                res.file_hash, res.total_pages, extracted_pages_count,
                1 if is_scanned else 0, status, res.error_message
            ))
            doc_id = cursor.lastrowid
        return doc_id

    def _save_chunks(
        self,
        doc_id: int,
        chunks: List[Dict[str, Any]],
        can_embed: bool = False,
        embed_model: Optional[str] = None
    ) -> int:
        """Insert chunk records and optional embeddings in one transaction."""
        rows = self._prepare_chunk_rows(chunks, can_embed, embed_model)
        with self.get_connection() as conn:
            return self._insert_chunk_rows(conn, doc_id, rows)

    def _prepare_chunk_rows(self, chunks, can_embed, embed_model):
        rows = []
        for start in range(0, len(chunks), 32):
            batch = chunks[start:start + 32]
            vectors = (
                self.ollama.get_batch_embeddings([c["text"] for c in batch], model=embed_model)
                if can_embed and embed_model else [None] * len(batch)
            )
            if len(vectors) != len(batch):
                raise ValueError("Embedding count does not match chunk count")
            if can_embed and embed_model and any(not vec for vec in vectors):
                raise RuntimeError("Embedding backend did not return every requested vector")
            for c, vec in zip(batch, vectors):
                rows.append((c["book_title"], c["filename"], c["page_num"],
                             c["chunk_index"], c["text"], pack_vector(vec) if vec else None))
        return rows

    @staticmethod
    def _insert_chunk_rows(conn, doc_id, rows):
        conn.executemany("""
            INSERT INTO chunks (doc_id, book_title, filename, page_num, chunk_index, text, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [(doc_id, *row) for row in rows])
        return len(rows)

    def get_status(self) -> Dict[str, Any]:
        """Get summary statistics of the current knowledge base."""
        with self.get_connection() as conn:
            doc_count = conn.execute("SELECT COUNT(*) as c FROM documents").fetchone()["c"]
            scanned_count = conn.execute("SELECT COUNT(*) as c FROM documents WHERE is_scanned = 1").fetchone()["c"]
            chunk_count = conn.execute("SELECT COUNT(*) as c FROM chunks").fetchone()["c"]
            embedded_chunk_count = conn.execute("SELECT COUNT(*) as c FROM chunks WHERE embedding IS NOT NULL").fetchone()["c"]
            total_pages = conn.execute("SELECT SUM(extracted_pages_count) as c FROM documents").fetchone()["c"] or 0
            
            docs = conn.execute("""
                SELECT id, filename, file_hash, clean_title, total_pages, extracted_pages_count, is_scanned, status, error_message, updated_at
                FROM documents ORDER BY filename ASC
            """).fetchall()

            # Count current explicit reviews by page identity. A fresh engine
            # draft cannot withdraw approval, but a later editor review can.
            from app.vision_ocr import CACHE_DIR
            captured, reviewed, latest_reviews = {}, {}, {}
            for cp in CACHE_DIR.glob("*.json"):
                try:
                    entry = json.loads(cp.read_text(encoding="utf-8"))
                    if not isinstance(entry, dict):
                        continue
                    key = (entry.get("source_relpath"), entry.get("source_hash"))
                    page = entry.get("page_num")
                    if type(page) is not int or page < 1:
                        continue
                    if entry.get("status") == "CAPTURED_PENDING_REVIEW" or entry.get("text"):
                        captured.setdefault(key, set()).add(page)
                    if entry.get("is_verified") or entry.get("review_schema") or entry.get("verified_by"):
                        identity = (key, page)
                        order = (entry.get("verified_at") or "", cp.stat().st_mtime_ns, cp.name)
                        previous = latest_reviews.get(identity)
                        if previous is None or order > previous[0]:
                            latest_reviews[identity] = (order, entry)
                except (OSError, ValueError, TypeError):
                    continue
            for (key, page), (_, entry) in latest_reviews.items():
                if entry.get("is_verified") and not entry.get("needs_review") and entry.get("text"):
                    reviewed.setdefault(key, set()).add(page)
            documents = []
            for row in docs:
                d = dict(row)
                key = (d["filename"], d["file_hash"])
                c = {p for p in captured.get(key, set()) if p <= d["total_pages"]}
                r = {p for p in reviewed.get(key, set()) if p <= d["total_pages"]}
                d.update(ocr_captured_pages=len(c), ocr_reviewed_pages=len(r),
                         ocr_pending_review_pages=len(c-r))
                documents.append(d)
            return {
                "total_documents": doc_count,
                "scanned_documents": scanned_count,
                "total_indexed_pages": total_pages,
                "total_chunks": chunk_count,
                "embedded_chunks": embedded_chunk_count,
                "ocr_captured_pages": sum(d["ocr_captured_pages"] for d in documents),
                "ocr_reviewed_pages": sum(d["ocr_reviewed_pages"] for d in documents),
                "ocr_pending_review_pages": sum(d["ocr_pending_review_pages"] for d in documents),
                "documents": documents
            }

    def update_page_chunks(self, filename: str, page_num: int, text: str) -> Dict[str, Any]:
        """Update chunks, embeddings, and full-text search for an affected page after human review."""
        if type(page_num) is not int or page_num < 1 or not isinstance(text, str) or not text.strip():
            raise ValueError("Trang hoặc nội dung đã duyệt không hợp lệ")
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT id, filename, clean_title, total_pages, is_scanned FROM documents WHERE filename = ?",
                (filename,)
            ).fetchone()
            if not row:
                logger.warning(f"Không tìm thấy tài liệu {filename} trong documents để cập nhật page chunks.")
                return {"status": "not_found", "chunks_updated": 0}

            doc_id = row["id"]
            clean_title = row["clean_title"]
            rel_filename = row["filename"]
            if page_num > row["total_pages"]:
                raise ValueError("Trang được duyệt nằm ngoài tài liệu")

        # Prepare all chunks before replacing an approved page. Keep the text,
        # FTS triggers and document counters inside one transaction.
        chunk_records = TextChunker.chunk_page(clean_title, rel_filename, page_num, text)
        with self.get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE doc_id = ? AND page_num = ?", (doc_id, page_num))
            for chunk in chunk_records:
                conn.execute("""INSERT INTO chunks
                    (doc_id,book_title,filename,page_num,chunk_index,text,embedding)
                    VALUES (?,?,?,?,?,?,NULL)""", (doc_id,clean_title,rel_filename,page_num,
                    chunk["chunk_index"],chunk["text"]))
            pages = conn.execute("SELECT COUNT(DISTINCT page_num) FROM chunks WHERE doc_id=?", (doc_id,)).fetchone()[0]
            state = "indexed" if pages >= row["total_pages"] else ("ocr_partial_reviewed" if row["is_scanned"] else "indexed")
            conn.execute("UPDATE documents SET extracted_pages_count=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (pages,state,doc_id))
        inserted = len(chunk_records)

        logger.info(f"Đã cập nhật {inserted} chunks cho tài liệu '{rel_filename}' trang {page_num} sau khi review OCR.")
        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": rel_filename,
            "page_num": page_num,
            "chunks_updated": inserted,
        }
