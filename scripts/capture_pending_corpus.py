"""Capture only frozen pending pages; never approve or start training.

Keeps original PDF rasters and two literal CPU OCR observations for comparison.
Approved reviews and indexed passages are untouched by this capture stage.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import subprocess
import time
from datetime import datetime, timezone

import pymupdf


def digest(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def atomic_json(path, record):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    temporary.replace(path)


def capture(row, destination, apple_engine):
    tag = row['source_sha256'] + '-' + str(row['page_num'])
    image = destination / 'images' / (tag + '.png')
    record_path = destination / 'pages' / (tag + '.json')
    if record_path.exists():
        previous = json.loads(record_path.read_text())
        if previous.get('status') == 'FAILED':
            # Preserve the failure for diagnosis; never retry an unchanged blocker.
            return 'FAILED', row['filename'], row['page_num'], True
        if (previous.get('status') == 'CAPTURED_PENDING_REVIEW'
                and previous['source_hash'] == row['source_sha256']
                and previous['image_hash'] == digest(image)
                and previous['apple_engine_sha256'] == digest(apple_engine)):
            return previous['status'], row['filename'], row['page_num'], True
        # Preserve failed observations; a new attempt is saved separately.
        history = destination / 'attempts'
        history.mkdir(exist_ok=True)
        (history / (tag + '-' + str(time.time_ns()) + '.json')).write_text(
            record_path.read_text())
    started = time.monotonic()
    record = dict(source_relpath=row['filename'], page_num=row['page_num'],
                  source_hash=row['source_sha256'], status='RUNNING',
                  image_path=str(image.resolve()), is_verified=False,
                  needs_review=True, apple_engine_sha256=digest(apple_engine),
                  created_at=datetime.now(timezone.utc).isoformat())
    try:
        with pymupdf.open(row['filepath']) as pdf:
            page = pdf[row['page_num'] - 1]
            page.get_pixmap(dpi=150, colorspace=pymupdf.csRGB, alpha=False).save(image)
            record['native_text'] = page.get_text('text')
        record['image_hash'] = digest(image)
        result = subprocess.run([str(apple_engine), str(image)], capture_output=True,
                                text=True, timeout=120, check=True)
        observation = json.loads(result.stdout)
        if not observation.get('success'):
            raise RuntimeError(observation.get('error', 'Apple OCR failed'))
        record['apple_observation'] = observation
        record['raw_text'] = '\n'.join(line['text'] for line in observation['lines'])
        result = subprocess.run(['tesseract', str(image), 'stdout', '-l', 'vie+eng',
                                 '--psm', '3'], capture_output=True, text=True,
                                timeout=120, check=True,
                                env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
        record['tesseract_text'] = result.stdout
        record['tesseract_stderr'] = result.stderr
        record['text'] = record['raw_text']
        record['status'] = 'CAPTURED_PENDING_REVIEW'
    except Exception as exc:
        record.update(status='FAILED', error=str(exc), error_type=type(exc).__name__)
    record['duration_seconds'] = time.monotonic() - started
    atomic_json(record_path, record)
    return record['status'], row['filename'], row['page_num'], False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--engine', type=pathlib.Path, required=True)
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--states', nargs='+', default=['ocr_pending_review'],
                        choices=('ocr_pending_review', 'visual_content_pending'))
    args = parser.parse_args()
    rows = json.loads(args.inventory.read_text())['records']
    rows = [r for r in rows if r['state'] in args.states]
    if args.limit:
        rows = rows[:args.limit]
    for name, expected in {(r['filepath'], r['source_sha256']) for r in rows}:
        if digest(name) != expected:
            raise RuntimeError('Source changed before capture: ' + name)
    for folder in ('images', 'pages'):
        (args.output / folder).mkdir(parents=True, exist_ok=True)
    status = dict(total=len(rows), captured=0, failed=0, resumed=0,
                  approved=0, state='RUNNING', training='NOT_RUN')
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(capture, r, args.output, args.engine.resolve()) for r in rows]
        for future in concurrent.futures.as_completed(futures):
            state, filename, page, resumed = future.result()
            status['captured' if state == 'CAPTURED_PENDING_REVIEW' else 'failed'] += 1
            status['resumed'] += int(resumed)
            status['last_page'] = dict(filename=filename, page=page, status=state)
            status['updated_at'] = datetime.now(timezone.utc).isoformat()
            atomic_json(args.output / 'progress.json', status)
            print(json.dumps(status, ensure_ascii=False), flush=True)
    status['state'] = 'RAW_CAPTURE_COMPLETE' if not status['failed'] else 'CAPTURE_HAS_FAILURES'
    atomic_json(args.output / 'progress.json', status)


if __name__ == '__main__':
    main()
