import asyncio
import json
import pymupdf
from app.indexer import KnowledgeIndexer
from app.pdf_extractor import PDFExtractor


def test_explicit_empty_review_supersedes_earlier_approved_text(tmp_path, monkeypatch):
    """An editor withdrawing a transcript must reduce current reviewed coverage."""
    src = tmp_path / 'src'; src.mkdir()
    doc = pymupdf.open(); doc.new_page(); doc.save(src / 'notes.pdf'); doc.close()
    indexer = KnowledgeIndexer(tmp_path / 'index.db', src)
    extracted = PDFExtractor.extract_pdf(src / 'notes.pdf')
    indexer._save_document_record(extracted, 'scanned_unocred', True)
    cache = tmp_path / 'cache'; cache.mkdir()
    monkeypatch.setattr('app.vision_ocr.CACHE_DIR', cache)
    common = {'source_relpath': 'notes.pdf', 'source_hash': extracted.file_hash,
              'page_num': 1, 'status': 'CAPTURED_PENDING_REVIEW'}
    older = dict(common, text='Incorrect topic presented as transcript', is_verified=True,
                 needs_review=False, verified_by='Editor', verified_at='2026-10-04T01:00:00Z')
    newer = dict(common, text='', is_verified=False, needs_review=True,
                 verified_by='Editor', verified_at='2026-10-04T02:00:00Z',
                 review_schema='ocr-region-review-v2')
    (cache / 'old.json').write_text(json.dumps(older))
    (cache / 'new.json').write_text(json.dumps(newer))
    page = indexer.get_status()['documents'][0]
    assert page['ocr_captured_pages'] == 1
    assert page['ocr_reviewed_pages'] == 0
    assert page['ocr_pending_review_pages'] == 1


def test_later_unreviewed_engine_draft_keeps_explicit_approval(tmp_path, monkeypatch):
    """A new engine attempt must not withdraw a reviewed transcript."""
    src = tmp_path / 'src'; src.mkdir()
    doc = pymupdf.open(); doc.new_page(); doc.save(src / 'notes.pdf'); doc.close()
    indexer = KnowledgeIndexer(tmp_path / 'index.db', src)
    extracted = PDFExtractor.extract_pdf(src / 'notes.pdf')
    indexer._save_document_record(extracted, 'scanned_unocred', True)
    cache = tmp_path / 'cache'; cache.mkdir()
    monkeypatch.setattr('app.vision_ocr.CACHE_DIR', cache)
    common = {'source_relpath': 'notes.pdf', 'source_hash': extracted.file_hash,
              'page_num': 1, 'status': 'CAPTURED_PENDING_REVIEW'}
    reviewed = dict(common, text='Reviewed source', is_verified=True, needs_review=False,
                    verified_by='Editor', verified_at='2026-10-04T01:00:00Z')
    draft = dict(common, text='Unreadable draft', is_verified=False, needs_review=True,
                 created_at='2026-10-04T03:00:00Z')
    (cache / 'approved.json').write_text(json.dumps(reviewed))
    (cache / 'draft.json').write_text(json.dumps(draft))
    page = indexer.get_status()['documents'][0]
    assert page['ocr_reviewed_pages'] == 1
    assert page['ocr_pending_review_pages'] == 0


def test_scan_progress_distinguishes_capture_review_and_indexing(tmp_path,monkeypatch):
    src=tmp_path/'src';src.mkdir()
    doc=pymupdf.open();doc.new_page();doc.new_page();doc.save(src/'notes.pdf');doc.close()
    indexer=KnowledgeIndexer(tmp_path/'index.db',src)
    extracted=PDFExtractor.extract_pdf(src/'notes.pdf')
    indexer._save_document_record(extracted,'scanned_unocred',True)
    cache=tmp_path/'cache';cache.mkdir()
    monkeypatch.setattr('app.vision_ocr.CACHE_DIR',cache)
    for key,page,verified in [('a',1,False),('b',1,True),('c',2,False)]:
        (cache/(key+'.json')).write_text(json.dumps({'source_relpath':'notes.pdf','source_hash':extracted.file_hash,'page_num':page,'status':'CAPTURED_PENDING_REVIEW','text':'Reviewed' if verified else 'Raw','is_verified':verified,'needs_review':not verified}))
    status=indexer.get_status()
    page=status['documents'][0]
    assert page['ocr_captured_pages']==2
    assert page['ocr_reviewed_pages']==1
    assert page['ocr_pending_review_pages']==1
    assert page['extracted_pages_count']==0


def test_review_keeps_saved_transcript_but_reports_index_failure(monkeypatch):
    from app import server
    from app.vision_ocr import VisionOCRManager
    monkeypatch.setattr(VisionOCRManager,'review_and_verify_transcript',lambda **kw:{'source_relpath':'notes.pdf','page_num':1,'text':'Reviewed','is_verified':True})
    def fail(**kw):raise RuntimeError('disk indexing failure')
    monkeypatch.setattr(server.indexer,'update_page_chunks',fail)
    req=server.OCRReviewRequest(cache_key='a'*64,corrected_text='Reviewed',reviewer_name='Reviewer')
    result=asyncio.run(server.submit_ocr_review(req))
    assert result['record']['is_verified']
    assert result['status']=='verified_not_indexed'
    assert result['index_update']['status']=='failed'
    assert 'disk indexing failure' in result['index_update']['error']
