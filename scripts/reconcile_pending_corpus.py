"""Exhaustive, resumable literal OCR reconciliation; never approve or index drafts.

All input pages get a source-bound outcome, including failures and partial sources.
Agreement between OCR engines is a review aid, not visual verification.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import difflib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import unicodedata

SCHEMA = 'whole-pending-reconciliation-v1'
ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f'.{os.getpid()}.{time.time_ns()}.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def compact(value):
    # Keep spelling, case, digits and punctuation. Only ignore layout whitespace.
    return re.sub(r'\s+', '', unicodedata.normalize('NFC', value))


def compare(left, right):
    a, b = compact(left), compact(right)
    if a == b:
        return {'exact_ignoring_layout': True, 'agreement': 1.0, 'differences': []}
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    differences = []
    for op, a0, a1, b0, b1 in matcher.get_opcodes():
        if op != 'equal':
            differences.append(dict(operation=op, left_offset=[a0, a1], right_offset=[b0, b1],
                                    left=a[a0:a1], right=b[b0:b1]))
    return {'exact_ignoring_layout': False, 'agreement': matcher.ratio(), 'differences': differences}


def resolve_capture(row):
    raw_path = row.get('raw_capture_path')
    review = None
    if not raw_path:
        review_path = Path(row['review_path'])
        review = json.loads(review_path.read_text())
        raw_path = review['raw_capture_path']
    raw_path = Path(raw_path)
    raw = json.loads(raw_path.read_text())
    image = Path(row.get('image_path') or raw.get('image_path') or review['image_path'])
    return raw_path, raw, image, review


def reconcile_one(row, output, root, recognize, engine_signature, source_hashes):
    key = signature({'filename': row['filename'], 'page_num': row['page_num']})
    path = output / 'pages' / f'{key}.json'
    result = dict(schema=SCHEMA, filename=row['filename'], page_num=row['page_num'],
                  source_sha256=row['source_sha256'], prior_state=row['state'],
                  queue_row_sha256=signature(row), engine_signature=engine_signature,
                  created_at=datetime.now(timezone.utc).isoformat(), is_verified=False,
                  needs_review=True, allowed_in_training=False, variants={}, errors=[],
                  state='EVIDENCE_CHANGED', source_image_reviewed=False)
    started = time.monotonic()
    try:
        source = (root / 'src' / row['filename']).resolve()
        if not source.is_relative_to((root / 'src').resolve()):
            raise ValueError('Source escapes corpus directory')
        result['source_current_sha256'] = source_hashes.get(row['filename'])
        if result['source_current_sha256'] != row['source_sha256']:
            result['state'] = 'SOURCE_CHANGED'
            raise ValueError('Actual source hash differs from queued source')
        raw_path, raw, image, review = resolve_capture(row)
        result.update(raw_capture_path=str(raw_path), raw_capture_sha256=digest(raw_path),
                      image_path=str(image), image_sha256=digest(image))
        if (raw['source_relpath'] != row['filename'] or raw['page_num'] != row['page_num']
                or raw['source_hash'] != row['source_sha256']
                or raw['image_hash'] != result['image_sha256']):
            raise ValueError('Source, page, raw capture and image do not match')
        if review and (review['image_sha256'] != result['image_sha256']
                       or review['raw_capture_sha256'] != result['raw_capture_sha256']):
            raise ValueError('Partial review evidence no longer matches')
        if path.exists():
            cached = json.loads(path.read_text())
            bindings = ['schema', 'queue_row_sha256', 'engine_signature', 'source_sha256',
                        'source_current_sha256', 'raw_capture_sha256', 'image_sha256']
            if all(cached.get(k) == result[k] for k in bindings):
                return cached
        result['variants'] = {'apple_vision': raw.get('raw_text', raw.get('text', '')),
                              'tesseract_original': raw.get('tesseract_text', ''),
                              'native_pdf': raw.get('native_text', '')}
        if row['state'] == 'visual_review_partial':
            result['state'] = 'SOURCE_PARTIAL'
            result['errors'].append('Known incomplete source review; no inferred restoration or approval')
            result['prior_review_path'] = row.get('review_path')
        else:
            for psm in (6, 11):
                try:
                    value = recognize(image, psm)
                    if not isinstance(value, str):
                        raise ValueError('OCR did not return literal text')
                    result['variants'][f'tesseract_psm{psm}'] = value
                except Exception as exc:
                    result['errors'].append(f'PSM {psm}: {type(exc).__name__}: {exc}')
            candidates = {k: v for k, v in result['variants'].items() if k != 'native_pdf'}
            result['comparisons'] = {k: compare(result['variants']['apple_vision'], v)
                                     for k, v in candidates.items() if k != 'apple_vision'}
            result['numeric_sequences'] = {k: re.findall(r'\d+(?:[.,:]\d+)*', v)
                                            for k, v in candidates.items()}
            result['code_symbol_sequences'] = {k: ''.join(re.findall(r'[{}\[\]<>!=;|]', v))
                                               for k, v in candidates.items()}
            result['source_type'] = ('code_or_formula' if re.search(
                r'\b(cout|cin|struct|enum)\b|\bfor\s*\(|\bint\s+main',
                result['variants']['apple_vision']) else 'visual' if row['state'] ==
                'visual_content_pending' else 'printed_text')
            if result['errors']:
                result['state'] = 'OCR_FAILED'
            elif not any(candidates.values()):
                result['state'] = 'IMAGE_CONTENT_REQUIRES_REVIEW'
            elif all(c['exact_ignoring_layout'] for c in result['comparisons'].values()):
                result['state'] = 'OCR_AGREEMENT_REQUIRES_VISUAL_REVIEW'
            else:
                result['state'] = 'OCR_DIFFERENCES_REQUIRE_VISUAL_REVIEW'
    except Exception as exc:
        result['errors'].append(f'{type(exc).__name__}: {exc}')
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    if path.exists():
        old = path.read_bytes()
        history = output / 'history' / f'{key}-{hashlib.sha256(old).hexdigest()}.json'
        if not history.exists():
            history.parent.mkdir(parents=True, exist_ok=True)
            history.write_bytes(old)
    write_json(path, result)
    return result


def run_queue(queue, output, root, recognize, engine_signature, workers=1):
    output, root = Path(output), Path(root)
    if workers not in (1, 2):
        raise ValueError('Bound CPU workers to 1 or 2')
    identities = [(x['filename'], x['page_num']) for x in queue]
    if len(set(identities)) != len(identities):
        raise ValueError('Duplicate pages in input queue')
    output.mkdir(parents=True, exist_ok=True)
    source_hashes = {}
    for name in sorted({x['filename'] for x in queue}):
        source = (root / 'src' / name).resolve()
        source_hashes[name] = digest(source) if source.is_relative_to((root / 'src').resolve()) and source.is_file() else None
    summary = dict(schema=SCHEMA, total=len(queue), processed=0, processing_complete=False,
                   queue_sha256=signature(queue), engine_signature=engine_signature,
                   is_verified=False, corpus_complete=False, training_started=False,
                   states={}, started_at=datetime.now(timezone.utc).isoformat(), pid=os.getpid())
    write_json(output / 'progress.json', summary)
    outcomes = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(reconcile_one, row, output, root, recognize,
                               engine_signature, source_hashes) for row in queue]
        for future in as_completed(futures):
            result = future.result()
            outcomes.append(result)
            summary.update(processed=len(outcomes), states=dict(Counter(x['state'] for x in outcomes)),
                           updated_at=datetime.now(timezone.utc).isoformat())
            write_json(output / 'progress.json', summary)
            if len(outcomes) % 20 == 0:
                print(json.dumps(summary, ensure_ascii=False), flush=True)
    source_after = {}
    for name in source_hashes:
        source = (root / 'src' / name).resolve()
        source_after[name] = digest(source) if source.is_relative_to((root / 'src').resolve()) and source.is_file() else None
    summary.update(processing_complete=len(outcomes) == len(queue), source_stable=source_after == source_hashes,
                   source_hashes_before=source_hashes, source_hashes_after=source_after,
                   finished_at=datetime.now(timezone.utc).isoformat())
    outcomes.sort(key=lambda x: (x['filename'], x['page_num']))
    write_json(output / 'outcomes.json', outcomes)
    write_json(output / 'summary.json', summary)
    write_json(output / 'progress.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if not k.startswith('source_hashes')},
                     ensure_ascii=False), flush=True)
    return summary


def recognize_tesseract(image, psm):
    completed = subprocess.run(['tesseract', str(image), 'stdout', '-l', 'vie+eng', '--psm', str(psm)],
                               env=dict(os.environ, OMP_THREAD_LIMIT='1'),
                               capture_output=True, text=True, timeout=90)
    if completed.returncode:
        raise RuntimeError(completed.stderr[-500:])
    return completed.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    executable = shutil.which('tesseract')
    if not executable:
        raise RuntimeError('Tesseract unavailable; no false completion')
    version = subprocess.run([executable, '--version'], capture_output=True, text=True, check=True).stdout
    languages = subprocess.run([executable, '--list-langs'], capture_output=True, text=True, check=True).stdout
    if not {'vie', 'eng'} <= set(languages.splitlines()):
        raise RuntimeError('Need actual vie+eng OCR language data')
    language_hashes = {}
    directory = re.search(r'"([^"]+)"', languages)
    if directory:
        for language in ('vie', 'eng'):
            path = Path(directory.group(1)) / f'{language}.traineddata'
            if path.is_file():
                language_hashes[language] = digest(path)
    engine = signature(dict(binary_sha256=digest(executable), version=version, languages=languages,
                            language_hashes=language_hashes, script_sha256=digest(__file__), psms=[6, 11]))
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / 'runner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write_json(args.output / 'engine.json', dict(signature=engine, version=version,
                                                   language_hashes=language_hashes))
        run_queue(json.loads(args.queue.read_text()), args.output, ROOT, recognize_tesseract,
                  engine, args.workers)


if __name__ == '__main__':
    main()
