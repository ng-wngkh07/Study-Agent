import importlib.util
import json
from pathlib import Path

import pymupdf


def test_raw_recapture_preserves_verified_transcript(tmp_path):
    import importlib.util
    path = Path(__file__).resolve().parents[1]/'scripts/capture_handwritten_corpus.py'
    spec = importlib.util.spec_from_file_location('capture_preservation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    approved = {'cache_key': 'page-key', 'text': 'Đã đối chiếu trang gốc', 'is_verified': True,
                'revisions': [{'text': 'Old draft'}]}
    destination = tmp_path/'page-key.json'
    destination.write_text(json.dumps(approved))
    module.publish_raw_draft({'cache_key': 'page-key', 'text': 'Wrong new OCR', 'is_verified': False}, tmp_path)
    assert json.loads(destination.read_text()) == approved
    assert any('Wrong new OCR' in p.read_text() for p in tmp_path.rglob('*.json') if p != destination)


def test_partial_capture_keeps_good_page_failure_and_does_not_approve_or_blind_retry(tmp_path):
    path = Path(__file__).resolve().parents[1]/'scripts/capture_handwritten_corpus.py'
    spec = importlib.util.spec_from_file_location('capture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    src = tmp_path/'src';src.mkdir()
    pdf = pymupdf.open();pdf.new_page();pdf.new_page();pdf.save(src/'notes.pdf');pdf.close()
    calls=[]
    def engine(image):
        calls.append(image)
        if len(calls)==2:
            raise RuntimeError('Actual OCR boundary failure')
        return {'success':True,'lines':[{'text':'Exact OCR draft','confidence':1.0}]}
    out=tmp_path/'capture'
    first=module.capture(['notes.pdf'],src,out,engine,'engine-test')
    assert first['captured']==1 and first['failed']==1
    records=[json.loads(p.read_text()) for p in (out/'pages').glob('*.json')]
    assert any(r.get('raw_text')=='Exact OCR draft' and not r['is_verified'] for r in records)
    assert any(r.get('error')=='Actual OCR boundary failure' for r in records)
    second=module.capture(['notes.pdf'],src,out,engine,'engine-test')
    assert len(calls)==2
    assert second['captured']==1 and second['failed']==1
    assert second['approved_for_training']==0
