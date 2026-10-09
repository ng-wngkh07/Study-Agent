"""Review acceptance must preserve the human/agent evidence claim."""
import importlib.util
import json
from pathlib import Path

import pymupdf
import pytest

from app.source_page_reviews import reviewed_page_text


def test_antigravity_editorial_does_not_claim_codex_authorship():
    text = reviewed_page_text({
        'kind': 'printed', 'transcript': 'Source text',
        'editorial': 'Additional explanation', 'unresolved': [],
        'reviewer': 'Antigravity direct visual review',
    })
    assert 'CỦA CODEX' not in text
    assert 'Additional explanation' in text
    assert 'KHÔNG PHẢI NGUYÊN VĂN' in text


def test_ledger_rejects_batch_without_explicit_visual_attestation(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / 'data/evaluation/corpus-completion-20261004/source_review_ledger.py'
    spec = importlib.util.spec_from_file_location('review_ledger_under_test', script)
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)
    monkeypatch.setattr(ledger, 'ROOT', tmp_path)
    monkeypatch.setattr(ledger, 'OUT', tmp_path / 'evaluation')
    monkeypatch.setattr(ledger, 'report', lambda: None)
    source = tmp_path / 'src' / 'sample.pdf'
    source.parent.mkdir()
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Source text')
        pdf.save(source)
    digest = ledger.sha(source)
    capture = ledger.OUT / 'source-captures' / digest
    capture.mkdir(parents=True)
    image = capture / '0001.png'
    with pymupdf.open(source) as pdf:
        pdf[0].get_pixmap().save(image)
    (capture / '0001.json').write_text(json.dumps({
        'source_relpath': 'sample.pdf', 'page_num': 1, 'source_hash': digest,
        'image_path': str(image), 'image_hash': ledger.sha(image),
    }))
    batch = tmp_path / 'batch.json'
    batch.write_text(json.dumps({'filename': 'sample.pdf', 'entries': [
        {'page': 1, 'transcript': 'Source text'},
    ]}))
    with pytest.raises(ValueError):
        ledger.save(batch)
    assert not list((ledger.OUT / 'source-reviews').glob('*/*.json'))
