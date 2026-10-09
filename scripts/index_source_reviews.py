"""Apply explicitly approved, source-bound page reviews, never raw OCR drafts."""
import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.chunker import TextChunker
from app.indexer import KnowledgeIndexer
from app.source_page_reviews import validate_page_review, reviewed_page_text, reviewed_page_state


def apply_reviews(paths, root=ROOT):
    indexer = KnowledgeIndexer(db_path=root / 'data/knowledge_base.db', src_dir=root / 'src')
    prepared = []
    # Validate the entire batch before any database writes.
    for path in paths:
        path = pathlib.Path(path).resolve()
        review = json.loads(path.read_text())
        source = (root / 'src' / review['filename']).resolve()
        if not source.is_relative_to((root / 'src').resolve()):
            raise ValueError('Source escapes corpus directory')
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        validate_page_review(review, review['filename'], review['page'], source_hash)
        if review['completeness'] != 'complete' or review.get('unresolved'):
            raise ValueError('Cannot release an incomplete page review')
        prepared.append((path, review, source_hash))
    with indexer.get_connection() as db:
        changed = []
        for path, review, source_hash in prepared:
            doc = db.execute('SELECT * FROM documents WHERE filename=?',
                             (review['filename'],)).fetchone()
            if not doc or doc['file_hash'] != source_hash or not 1 <= review['page'] <= doc['total_pages']:
                raise ValueError('Review and indexed document identity differ')
            expected = TextChunker.chunk_page(doc['clean_title'], review['filename'],
                                             review['page'], reviewed_page_text(review))
            actual = [r['text'] for r in db.execute(
                'SELECT text FROM chunks WHERE doc_id=? AND page_num=? ORDER BY chunk_index',
                (doc['id'], review['page']))]
            texts = [r['text'] for r in expected]
            if actual != texts:
                db.execute('DELETE FROM chunks WHERE doc_id=? AND page_num=?',
                           (doc['id'], review['page']))
                db.executemany('INSERT INTO chunks(doc_id,book_title,filename,page_num,chunk_index,text) '
                               'VALUES(?,?,?,?,?,?)',
                               [(doc['id'], doc['clean_title'], review['filename'], review['page'],
                                 r['chunk_index'], r['text']) for r in expected])
            state = reviewed_page_state(review)
            db.execute('INSERT OR REPLACE INTO corpus_source_pages VALUES(?,?,?,?,?,?,?,?)',
                       (review['filename'], review['page'], source_hash, state,
                        hashlib.sha256(json.dumps(texts, ensure_ascii=False).encode()).hexdigest(),
                        str(path), hashlib.sha256(path.read_bytes()).hexdigest(),
                        datetime.now(timezone.utc).isoformat()))
            db.execute('UPDATE documents SET extracted_pages_count=(SELECT count(DISTINCT page_num) '
                       'FROM chunks WHERE doc_id=?) WHERE id=?', (doc['id'], doc['id']))
            changed.append(dict(filename=review['filename'], page=review['page'], state=state,
                                text_changed=actual != texts, chunks=len(texts)))
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reviews', type=pathlib.Path, required=True)
    parser.add_argument('--report', type=pathlib.Path, required=True)
    args = parser.parse_args()
    changed = apply_reviews(json.loads(args.reviews.read_text()))
    args.report.write_text(json.dumps(changed, ensure_ascii=False, indent=2))
    print('Approved page reviews indexed:', len(changed))
