"""Compute actual sample/source/token exposure before a corpus-complete trial."""
import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

DOMAINS = ('linear_algebra', 'calculus', 'discrete_math', 'programming', 'physics', 'psychology')
ALIASES = {'algebra': 'linear_algebra', 'computer_science': 'programming', 'cpp': 'programming',
           'data_structures': 'programming', 'oop': 'programming', 'algorithms': 'programming',
           'study_habits': 'psychology'}


def assess_exposure(records, token_lengths=None):
    failures = []
    counts = {split: Counter() for split in ('train', 'valid')}
    sources = defaultdict(Counter)
    exposure = Counter()
    for row in records:
        domain = ALIASES.get(row['domain'], row['domain'])
        split = row['split']
        if domain not in DOMAINS or split not in counts:
            failures.append('unknown_domain_or_split'); continue
        counts[split][domain] += 1
        if not row.get('source_file_sha256'):
            failures.append('missing_content_source_group'); continue
        if split=='train':
            sources[domain][row['source_file_sha256']] += 1
            if token_lengths is not None:
                exposure[domain] += token_lengths[row['id']]
    for split, dist in counts.items():
        total = sum(dist.values())
        for domain in DOMAINS:
            fraction = dist[domain]/total if total else 0
            # Six equally weighted subjects, with a quarter tolerance for counts.
            if not (0.75/6 <= fraction <= 1.25/6):
                failures.append(f'{split}_unbalanced:{domain}')
    for domain in DOMAINS:
        dist = sources[domain]
        if len(dist)<2 or (dist and max(dist.values())/sum(dist.values()) > 0.5):
            failures.append('source_concentration:'+domain)
    if token_lengths is not None:
        total = sum(exposure.values())
        for domain in DOMAINS:
            fraction = exposure[domain]/total if total else 0
            if not (0.5/6 <= fraction <= 1.5/6):
                failures.append('target_token_exposure:'+domain)
    return {'counts': {k:dict(v) for k,v in counts.items()},
            'distinct_train_source_groups': {k:len(sources[k]) for k in DOMAINS},
            'target_tokens': dict(exposure), 'failures': failures, 'passed': not failures,
            'exact_token_exposure_measured': token_lengths is not None}


def exact_balance(data_dir, model_dir):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
    records = [json.loads(s) for s in (data_dir/'approved_manifest.jsonl').read_text().splitlines()]
    lengths = {}
    for split in ('train','valid'):
        manifest = [r for r in records if r['split']==split]
        examples = [json.loads(s) for s in (data_dir/f'{split}.jsonl').read_text().splitlines()]
        if len(manifest)!=len(examples): raise ValueError('Manifest/example counts differ')
        for row, example in zip(manifest, examples):
            messages = example['messages']
            prompt = '\n'.join(m['content'] for m in messages[:-1] if m['role'] in ('system','user'))
            if not row.get('passage') or row['passage'] not in prompt:
                raise ValueError('Training input missing exact source passage at '+row['id'])
            # Existing source/target gates still apply; bind exposure to the actual answers.
            if messages[-1]['role']!='assistant' or messages[-1]['content'].strip()!=row['reference'].strip():
                raise ValueError('Manifest/answer order differs at '+row['id'])
            lengths[row['id']] = len(tokenizer.encode(messages[-1]['content'], add_special_tokens=False))
    report = assess_exposure(records, lengths)
    report['source_context_bound'] = True
    report['manifest_sha256'] = hashlib.sha256((data_dir/'approved_manifest.jsonl').read_bytes()).hexdigest()
    report['dataset_sha256'] = hashlib.sha256((data_dir/'train.jsonl').read_bytes()+(data_dir/'valid.jsonl').read_bytes()).hexdigest()
    return report


def require_balanced_dataset(root, data_dir, model_dir):
    if not (root/'data/runtime/corpus_completion_policy.json').exists(): return None
    proc = subprocess.run([str(root/'.train-venv/bin/python'), '-m', 'app.dataset_balance',
        '--data',str(data_dir),'--model',str(model_dir)], cwd=root, capture_output=True, text=True, timeout=120)
    if proc.returncode:
        raise RuntimeError('DATASET_UNBALANCED: không xác minh được tỷ lệ nguồn/token: '+proc.stderr[-400:])
    report = json.loads(proc.stdout)
    if not report['passed'] or not report['exact_token_exposure_measured']:
        raise RuntimeError('DATASET_UNBALANCED: '+json.dumps(report['failures'],ensure_ascii=False))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',type=Path,required=True);parser.add_argument('--model',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(exact_balance(args.data,args.model),ensure_ascii=False))
