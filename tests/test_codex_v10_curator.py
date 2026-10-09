"""Integration over pinned parent/source fixtures; tokens mocked at external runtime boundary."""
import copy
import json
from pathlib import Path
from scripts.curate_v10 import ROOT, curate, sha, rows
from app.sample_ledger import SampleLedger


def test_bad_amendment_preserves_parent_and_earlier_good_sample(tmp_path):
    proposals=json.loads((ROOT/'data/evaluation/codex-v10-reviewed-growth-proposals-r2-2026-10-04.json').read_text())
    good=copy.deepcopy(next(p for p in proposals if p['id']=='NEW_TRAIN_SPECS-001' and p.get('review')))
    bad=copy.deepcopy(good);bad['span_end']+=1;bad['revision_reason']='Deliberately wrong boundary'
    release=tmp_path/'release';history=tmp_path/'history'
    report=curate([good,bad],release,history,token_counter=lambda ms:[471]*len(ms))
    assert (report['train_samples'],report['valid_samples'])==(30,6)
    parent=ROOT/'data/training/v9_multidomain_grounded'
    assert rows(release/'train.jsonl')[:29]==rows(parent/'train.jsonl')
    assert rows(release/'valid.jsonl')==rows(parent/'valid.jsonl')
    assert rows(release/'approved_manifest.jsonl')[:35]==rows(parent/'approved_manifest.jsonl')
    selected=[e for e in SampleLedger(history).accepted() if e['stable_id']==good['id']]
    assert len(selected)==1 and selected[0]['payload']['passage']==good['passage']
    assert any(e['stable_id']==good['id'] and e['status']=='quarantined' for e in SampleLedger(history).history())
    assert not report['training_approved']


def test_v11_retains_all_v10_and_quarantines_changed_ocr_binding(tmp_path):
    proposals = json.loads((ROOT/'data/evaluation/ocr15-20261004/v11-reviewed-proposals.json').read_text())
    good = copy.deepcopy(next(p for p in proposals if p.get('source_type') == 'reviewed_ocr'))
    bad = copy.deepcopy(good)
    bad['ocr_record_sha256'] = '0'*64
    parent = ROOT/'data/training/v10_multidomain_grounded'
    release = tmp_path/'v11'
    history = tmp_path/'history'
    report = curate([good,bad],release,history,token_counter=lambda ms:[590]*len(ms),parent=parent)
    assert report['parent_retained'] == 123
    assert rows(release/'approved_manifest.jsonl')[:123] == rows(parent/'approved_manifest.jsonl')
    assert rows(release/'train.jsonl')[:101] == rows(parent/'train.jsonl')
    assert rows(release/'valid.jsonl') == rows(parent/'valid.jsonl')
    assert report['train_samples'] == 102
    events = SampleLedger(history).history()
    assert any(e['status']=='quarantined' and 'revision changed' in e['reason'] for e in events)
    assert next(e for e in SampleLedger(history).accepted() if e['stable_id']==good['id'])['payload']==good
