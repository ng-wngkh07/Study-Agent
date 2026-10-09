import hashlib
import json
from pathlib import Path

import pymupdf

from scripts.reconcile_pending_corpus import run_queue


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path):
    (tmp_path / 'src').mkdir()
    source = tmp_path / 'src' / 'book.pdf'
    with pymupdf.open() as doc:
        for text in ['Literal source 1', 'Literal source 2', 'Clipped source']:
            page = doc.new_page(width=300, height=120)
            page.insert_text((20, 40), text)
        doc.save(source)
    queue = []
    with pymupdf.open(source) as doc:
        for i in range(3):
            image = tmp_path / f'page-{i+1}.png'
            doc[i].get_pixmap().save(image)
            raw = tmp_path / f'raw-{i+1}.json'
            raw.write_text(json.dumps(dict(source_relpath='book.pdf', page_num=i+1,
                source_hash=sha(source), image_path=str(image), image_hash=sha(image),
                text=f'Literal source {i+1}', tesseract_text=f'Literal source {i+1}')))
            queue.append(dict(filename='book.pdf', page_num=i+1, source_sha256=sha(source),
                state='visual_review_partial' if i == 2 else 'ocr_pending_review',
                raw_capture_path=str(raw), image_path=str(image), review_path=''))
    return queue


def records(output):
    return [json.loads(p.read_text()) for p in (output / 'pages').glob('*.json')]


def test_every_page_has_outcome_even_when_one_ocr_fails(tmp_path):
    queue = fixture(tmp_path)
    output = tmp_path / 'out'
    def recognize(image, psm):
        if image.name == 'page-2.png':
            raise RuntimeError('actual backend failure')
        return 'Literal source 1'
    result = run_queue(queue, output, tmp_path, recognize, 'engine-test')
    rows = records(output)
    assert result['processed'] == result['total'] == 3
    assert result['processing_complete'] is True
    assert len(rows) == 3
    assert next(x for x in rows if x['page_num'] == 2)['state'] == 'OCR_FAILED'
    assert next(x for x in rows if x['page_num'] == 3)['state'] == 'SOURCE_PARTIAL'
    assert all(x['is_verified'] is False for x in rows)


def test_identical_ocr_never_releases_source_or_training(tmp_path):
    queue = fixture(tmp_path)[:1]
    database = tmp_path / 'knowledge_base.db'
    database.write_bytes(b'unchanged database')
    before = sha(database)
    output = tmp_path / 'out'
    result = run_queue(queue, output, tmp_path, lambda image, psm: 'Literal source 1', 'engine-test')
    row = records(output)[0]
    assert result['processing_complete'] is True
    assert row['is_verified'] is False and row['needs_review'] is True
    assert row['allowed_in_training'] is False
    assert row['variants']['tesseract_psm6'] == 'Literal source 1'
    assert sha(database) == before


def test_changed_source_cannot_reuse_cached_success(tmp_path):
    queue = fixture(tmp_path)[:1]
    output = tmp_path / 'out'
    run_queue(queue, output, tmp_path, lambda image, psm: 'Literal source 1', 'engine-test')
    (tmp_path / 'src' / 'book.pdf').write_bytes(b'changed source')
    def forbidden(image, psm):
        raise AssertionError('OCR must not run against changed source')
    run_queue(queue, output, tmp_path, forbidden, 'engine-test')
    assert records(output)[0]['state'] == 'SOURCE_CHANGED'


def test_changed_image_cannot_reuse_cached_success(tmp_path):
    queue = fixture(tmp_path)[:1]
    output = tmp_path / 'out'
    run_queue(queue, output, tmp_path, lambda image, psm: 'Literal source 1', 'engine-test')
    Path(queue[0]['image_path']).write_bytes(b'changed image')
    run_queue(queue, output, tmp_path, lambda image, psm: 'untrusted', 'engine-test')
    assert records(output)[0]['state'] == 'EVIDENCE_CHANGED'


def test_changed_engine_requires_fresh_capture(tmp_path):
    queue = fixture(tmp_path)[:1]
    output = tmp_path / 'out'
    run_queue(queue, output, tmp_path, lambda image, psm: 'Literal source 1', 'engine-a')
    seen = []
    def fresh(image, psm):
        seen.append(psm)
        return 'new literal capture'
    run_queue(queue, output, tmp_path, fresh, 'engine-b')
    assert seen == [6, 11]
    assert records(output)[0]['engine_signature'] == 'engine-b'
