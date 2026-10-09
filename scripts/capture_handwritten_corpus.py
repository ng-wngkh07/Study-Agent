"""Capture every requested PDF page locally; keep drafts and failures resumable.

This stage never approves OCR or launches training. Original PDFs are read-only.
Native Vision is an independent draft, not proof of mathematical/code fidelity.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.vision_ocr import VisionOCRManager, BACKEND_APPLE_VISION, _atomic_write_cache


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def publish_raw_draft(record, cache_dir):
    destination = Path(cache_dir)/(record['cache_key']+'.json')
    if destination.exists():
        previous = json.loads(destination.read_text())
        if previous.get('is_verified'):
            # Preserve the approved revision; retain the fresh observation separately.
            draft_hash = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
            history = Path(cache_dir)/'raw_recaptures'
            history.mkdir(parents=True, exist_ok=True)
            _atomic_write_cache(history/(record['cache_key']+'-'+draft_hash+'.json'), record)
            return
    _atomic_write_cache(destination, record)


def capture(files, src_dir, output, engine, engine_digest, cache_writer=None):
    import pymupdf
    output = Path(output)
    images = output / 'images'
    pages = output / 'pages'
    images.mkdir(parents=True, exist_ok=True)
    pages.mkdir(parents=True, exist_ok=True)
    src_dir = Path(src_dir).resolve()
    inventory = []
    for name in files:
        source = (src_dir / name).resolve()
        if not source.is_relative_to(src_dir) or not source.is_file():
            raise ValueError('Source outside src or missing: ' + name)
        with pymupdf.open(source) as doc:
            count = len(doc)
        inventory.append({'filename': name, 'source_sha256': file_hash(source), 'pages': count})
    planned = output / 'inventory.json'
    if planned.exists():
        original = json.loads(planned.read_text())
        if original['documents'] != inventory or original['engine_digest'] != engine_digest:
            raise ValueError('Frozen inputs/engine changed: use a new capture directory')
    else:
        _atomic_write_cache(planned, {'documents': inventory, 'engine_digest': engine_digest,
            'dpi': 150, 'created_at': now(), 'total_pages': sum(d['pages'] for d in inventory)})
    state = {'status': 'RUNNING', 'started_at': now(), 'total_documents': len(inventory),
        'total_pages': sum(d['pages'] for d in inventory), 'captured': 0, 'failed': 0,
        'empty_drafts': 0, 'approved_for_training': 0, 'active_page': None}
    _atomic_write_cache(output / 'progress.json', state)
    for item in inventory:
        source = src_dir / item['filename']
        if file_hash(source) != item['source_sha256']:
            raise ValueError('Source changed during capture: ' + item['filename'])
        with pymupdf.open(source) as doc:
            for page_no in range(1, item['pages'] + 1):
                tag = item['source_sha256'] + '-' + str(page_no)
                record_path = pages / (tag + '.json')
                state['active_page'] = {'filename': item['filename'], 'page': page_no}
                _atomic_write_cache(output / 'progress.json', state)
                record = json.loads(record_path.read_text()) if record_path.exists() else None
                if record and record.get('status') in ('CAPTURED_PENDING_REVIEW', 'FAILED'):
                    # Resume only unfinished work. A failed attempt needs explicit
                    # diagnosed remediation and a new directory, never blind retry.
                    state['captured' if record['status'] == 'CAPTURED_PENDING_REVIEW' else 'failed'] += 1
                    state['empty_drafts'] += int(record.get('status') == 'CAPTURED_PENDING_REVIEW' and not record.get('raw_text'))
                    continue
                image_path = images / (tag + '.png')
                pix = doc[page_no - 1].get_pixmap(dpi=150, alpha=False)
                pix.save(image_path)
                options = {'dpi': 150, 'image_hash': file_hash(image_path), 'engine_digest': engine_digest,
                    'cpu_only': True, 'uses_language_correction': False}
                key = VisionOCRManager.compute_cache_key(item['source_sha256'], page_no,
                    BACKEND_APPLE_VISION, engine_digest, 'apple-literal-draft-v1', options)
                record = {'status': 'RUNNING', 'cache_key': key, 'source_hash': item['source_sha256'],
                    'source_relpath': item['filename'], 'page_num': page_no, 'backend': BACKEND_APPLE_VISION,
                    'model': 'macOS Vision VNRecognizeTextRequest', 'model_digest': engine_digest,
                    'prompt_version': 'apple-literal-draft-v1', 'ocr_type': 'neural_vision',
                    'options': options, 'image_hash': options['image_hash'], 'image_path': str(image_path.resolve()),
                    'handwriting_suspected': True, 'needs_review': True, 'is_verified': False,
                    'verified_by': None, 'verified_at': None, 'verification_notes': None,
                    'revisions': [], 'created_at': now(),
                    'disclaimer': 'Bản OCR tự động chưa đối chiếu. Công thức, ký hiệu và mã nguồn có thể sai; không dùng làm mẫu huấn luyện đã duyệt.'}
                _atomic_write_cache(record_path, record)
                started = time.monotonic()
                try:
                    result = engine(image_path)
                    if not result.get('success'):
                        raise RuntimeError(result.get('error', 'OCR did not complete'))
                    lines = result.get('lines')
                    if not isinstance(lines, list) or any(not isinstance(v.get('text'), str) for v in lines):
                        raise ValueError('Invalid actual OCR lines')
                    text = '\n'.join(v['text'] for v in lines)
                    record.update(status='CAPTURED_PENDING_REVIEW', raw_text=text, text=text,
                        raw_engine_result=result, finished_at=now(), duration_seconds=round(time.monotonic()-started, 3))
                    if cache_writer:
                        cache_writer(record)
                    state['captured'] += 1
                    state['empty_drafts'] += int(not text.strip())
                except Exception as exc:
                    record.update(status='FAILED', error_type=type(exc).__name__, error=str(exc),
                        finished_at=now(), duration_seconds=round(time.monotonic()-started, 3))
                    state['failed'] += 1
                _atomic_write_cache(record_path, record)
                _atomic_write_cache(output / 'progress.json', state)
                print(json.dumps({'file': item['filename'], 'page': page_no, 'status': record['status'],
                    'captured': state['captured'], 'failed': state['failed']}, ensure_ascii=False), flush=True)
    state.update(status='CAPTURE_COMPLETE_WITH_ERRORS' if state['failed'] else 'RAW_CAPTURE_COMPLETE',
        finished_at=now(), active_page=None)
    _atomic_write_cache(output / 'progress.json', state)
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    engine_path = args.engine.resolve()
    digest = hashlib.sha256((file_hash(engine_path) + platform.mac_ver()[0]).encode()).hexdigest()
    def engine(image_path):
        result = subprocess.run([str(engine_path), str(image_path)], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(result.stdout[:1000] + result.stderr[:1000])
        return json.loads(result.stdout)
    from app.vision_ocr import CACHE_DIR
    capture(json.loads(args.files.read_text()), ROOT/'src', args.output, engine, digest,
        cache_writer=lambda record: publish_raw_draft(record, CACHE_DIR))


if __name__ == '__main__':
    main()
