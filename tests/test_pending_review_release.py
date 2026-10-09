import hashlib
import json

import pymupdf
import pytest

from app.indexer import KnowledgeIndexer
from scripts.index_source_reviews import apply_reviews


@pytest.fixture
def source_review(tmp_path):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'data').mkdir()
    source = tmp_path / 'src' / 'source.pdf'
    pdf = pymupdf.open()
    pdf.new_page().insert_text((40, 40), 'Actual source passage.')
    pdf.new_page()
    pdf.save(source)
    indexer = KnowledgeIndexer(db_path=tmp_path / 'data/knowledge_base.db', src_dir=tmp_path / 'src')
    indexer.index_all(embed_model=None)
    with indexer.get_connection() as db:
        db.execute('CREATE TABLE corpus_source_pages(filename TEXT,page_num INTEGER,source_sha256 TEXT,'
                   'state TEXT,chunks_sha256 TEXT,review_path TEXT,review_sha256 TEXT,checked_at TEXT,'
                   'PRIMARY KEY(filename,page_num))')
    image = tmp_path / 'page.png'
    with pymupdf.open(source) as pdf:
        pdf[0].get_pixmap(alpha=False).save(image)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    raw = tmp_path / 'raw.json'
    raw.write_text(json.dumps(dict(source_relpath='source.pdf', page_num=1,
                                   source_hash=sha(source), image_hash=sha(image))))
    record = dict(filename='source.pdf', page=1, source_sha256=sha(source),
                  image_path=str(image), image_sha256=sha(image), raw_capture_path=str(raw),
                  raw_capture_sha256=sha(raw), image_reviewed=True, completeness='complete',
                  kind='text', transcript='Actual source passage.', unresolved=[], editorial='')
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(record))
    return tmp_path, indexer, path, record


def test_partial_review_batch_cannot_change_even_first_approved_page(source_review):
    root, indexer, path, record = source_review
    partial = root / 'partial.json'
    partial.write_text(json.dumps({**record, 'completeness': 'partial', 'unresolved': ['Cut-off source']}))
    with indexer.get_connection() as db:
        before = [tuple(r) for r in db.execute('SELECT id,text FROM chunks')]
    with pytest.raises(ValueError, match='incomplete'):
        apply_reviews([path, partial], root)
    with indexer.get_connection() as db:
        assert before == [tuple(r) for r in db.execute('SELECT id,text FROM chunks')]
        assert db.execute('SELECT count(*) FROM corpus_source_pages').fetchone()[0] == 0


def test_changed_source_cannot_be_released(source_review):
    root, _, path, _ = source_review
    with (root / 'src/source.pdf').open('ab') as stream:
        stream.write(b'\nsource changed')
    with pytest.raises(ValueError, match='Invalid review identity'):
        apply_reviews([path], root)


def test_changed_image_cannot_be_released(source_review):
    root, _, path, record = source_review
    with open(record['image_path'], 'ab') as stream:
        stream.write(b'changed evidence')
    with pytest.raises(ValueError, match='Changed review evidence'):
        apply_reviews([path], root)


def test_approved_source_passage_and_review_binding_are_indexed(source_review):
    root, indexer, path, _ = source_review
    result = apply_reviews([path], root)
    assert result[0]['state'] == 'text_verified'
    with indexer.get_connection() as db:
        row = db.execute('SELECT * FROM corpus_source_pages').fetchone()
        assert row['review_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
        text = db.execute('SELECT text FROM chunks WHERE page_num=1').fetchone()[0]
        assert 'Actual source passage.' in text
        assert db.execute('SELECT embedding FROM chunks WHERE page_num=1').fetchone()[0] is None
    # Releasing a passage never fabricates a vector or starts training.


def test_visual_only_review_preserves_image_without_fabricating_source_text(source_review):
    root, indexer, path, record = source_review
    record.update(kind='visual', transcript='', visible_text_status='none',
                  visual_description='Black silhouette with a speech bubble.')
    path.write_text(json.dumps(record))
    result = apply_reviews([path], root)
    assert result[0]['state'] == 'visual_verified'
    with indexer.get_connection() as db:
        text = db.execute('SELECT text FROM chunks WHERE page_num=1').fetchone()[0]
        assert 'MÔ TẢ HÌNH' in text
        assert 'KHÔNG PHẢI NGUYÊN VĂN' in text
        assert 'NỘI DUNG NGUỒN ĐÃ ĐỐI CHIẾU' not in text
        assert db.execute('SELECT review_path FROM corpus_source_pages').fetchone()[0] == str(path)


@pytest.mark.parametrize('fault', ['missing_description', 'unreadable_text'])
def test_visual_kind_cannot_hide_unreviewed_content(source_review, fault):
    root, _, path, record = source_review
    record.update(kind='visual', transcript='', visible_text_status='none',
                  visual_description='Visible artwork.')
    if fault == 'missing_description':
        record['visual_description'] = ''
    else:
        record['visible_text_status'] = 'unreadable'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        apply_reviews([path], root)
