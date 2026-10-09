"""Verified handwriting fragments survive uncertain neighbouring regions."""
import hashlib
import json

import pytest

from app.vision_ocr import VisionOCRManager


def digest(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def raw(tmp_path, monkeypatch):
    src = tmp_path / 'src'
    src.mkdir()
    cache = tmp_path / 'cache'
    cache.mkdir()
    source = src / 'notes.pdf'
    source.write_bytes(b'unchanged source fixture')
    image = tmp_path / 'page.png'
    image.write_bytes(b'source image fixture')
    monkeypatch.setattr('app.vision_ocr.SRC_DIR', src)
    monkeypatch.setattr('app.vision_ocr.CACHE_DIR', cache)
    entry = {'cache_key': 'a' * 64, 'source_hash': digest(source.read_bytes()),
             'source_relpath': source.name, 'page_num': 1,
             'image_path': str(image), 'image_hash': digest(image.read_bytes()),
             'text': 'OCR raw: correct line, wrong symbol, unreadable line',
             'is_verified': False, 'needs_review': True}
    path = cache / (entry['cache_key'] + '.json')
    path.write_text(json.dumps(entry))
    return entry, path, source, image


def regions():
    return [
        {'id': 'clear', 'bbox': [0, 0, 1, .2], 'status': 'verified',
         'text': 'f(u+v)=f(u)+f(v)', 'reason': 'Read directly from source image'},
        {'id': 'fixed', 'bbox': [0, .2, 1, .4], 'status': 'corrected',
         'text': 'f(αu)=αf(u)', 'reason': 'OCR alpha corrected against source image'},
        {'id': 'unclear', 'bbox': [0, .4, 1, .6], 'status': 'unreadable',
         'text': 'Raw uncertain guess', 'reason': 'Illegible handwriting'},
        {'id': 'rest', 'bbox': [0, .6, 1, 1], 'status': 'pending',
         'text': '', 'reason': 'Not yet reviewed'},
        {'id': 'explanation', 'bbox': [0, 0, 1, .4], 'status': 'derived_explanation',
         'text': 'Teaching explanation beyond the literal handwriting',
         'reason': 'Separate educational addition'},
    ]


def test_partial_regions_keep_only_verified_text_and_preserve_raw(raw):
    entry, path, _, _ = raw
    before = path.read_bytes()
    result = VisionOCRManager.review_regions(entry['cache_key'], regions(), 'Codex')
    assert result['text'] == 'f(u+v)=f(u)+f(v)\nf(αu)=αf(u)'
    assert result['is_verified'] is True
    assert result['full_page_text_reviewed'] is False
    assert result['regions'] == regions()
    assert result['parent_record_sha256'] == digest(before)
    assert result['cache_key'] != entry['cache_key']
    assert path.read_bytes() == before
    assert VisionOCRManager.is_allowed_in_training(result)[0] is True


def test_all_uncertain_regions_are_retained_without_training_approval(raw):
    entry, _, _, _ = raw
    result = VisionOCRManager.review_regions(entry['cache_key'], regions()[2:], 'Codex')
    assert result['text'] == ''
    assert result['regions'] == regions()[2:]
    assert result['is_verified'] is False
    assert VisionOCRManager.is_allowed_in_training(result)[0] is False


def test_image_binding_mismatch_cannot_approve_text(raw):
    entry, _, _, image = raw
    image.write_bytes(b'changed')
    with pytest.raises(ValueError, match='image|ảnh'):
        VisionOCRManager.review_regions(entry['cache_key'], regions(), 'Codex')


def test_changed_source_cannot_approve_text(raw):
    entry, _, source, _ = raw
    source.write_bytes(b'changed')
    with pytest.raises(ValueError, match='source|Nguồn'):
        VisionOCRManager.review_regions(entry['cache_key'], regions(), 'Codex')


@pytest.mark.parametrize('change', [{'bbox': [0, 0, 2, 1]}, {'status': 'guessed'}, {'text': ''}])
def test_invalid_verified_region_rejected(raw, change):
    entry, _, _, _ = raw
    bad = regions()
    bad[0].update(change)
    with pytest.raises(ValueError):
        VisionOCRManager.review_regions(entry['cache_key'], bad, 'Codex')


def test_identical_review_reuses_revision_without_rewriting(raw):
    entry, _, _, _ = raw
    first = VisionOCRManager.review_regions(entry['cache_key'], regions(), 'Codex')
    second = VisionOCRManager.review_regions(entry['cache_key'], regions(), 'Codex')
    assert second == first


def test_training_gate_rejects_text_added_outside_verified_regions(raw):
    entry, _, _, _ = raw
    result = VisionOCRManager.review_regions(entry['cache_key'], regions(), 'Codex')
    result['text'] += '\nUnverified added claim'
    assert VisionOCRManager.is_allowed_in_training(result)[0] is False


def test_manual_region_review_preserves_code_identifiers_and_indentation(raw):
    entry, _, _, _ = raw
    code = 'int getHeight(AVLNodes *x) {\n    return x->height;\n}'
    rs = [{'id': 'code', 'bbox': [0, 0, 1, 1], 'status': 'corrected',
           'text': code, 'reason': 'Compared exact handwritten code identifiers'}]
    result = VisionOCRManager.review_regions(entry['cache_key'], rs, 'Codex')
    assert result['text'] == code
    assert VisionOCRManager.is_allowed_in_training(result)[0] is True


def test_legacy_manual_review_preserves_verified_code_as_written(raw):
    entry, path, _, _ = raw
    code = 'int getHeight(AVLNodes *x) {\n    return x->height;\n}'
    result = VisionOCRManager.review_and_verify_transcript(entry['cache_key'], code, 'Codex')
    assert result['text'] == code
    assert result['revisions'][0]['text'] == entry['text']
