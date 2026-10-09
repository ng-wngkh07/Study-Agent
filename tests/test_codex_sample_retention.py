import hashlib
import pytest
from app.sample_ledger import SampleLedger


def proof(answer):
    return {'reviewer':'Codex','grade':'pass','source_verified':True,
            'answer_sha256':hashlib.sha256(answer.encode()).hexdigest()}


def test_one_bad_sample_keeps_good_samples_and_failure_reason(tmp_path):
    ledger=SampleLedger(tmp_path)
    row={'reference':'Faithful answer','source_file':'native.pdf','source_file_sha256':'a'*64,'page':2}
    ledger.record('good',row,'accepted','Verified',proof(row['reference']))
    ledger.record('bad',{'reference':'Unchecked answer'},'quarantined','Page anchor missing')
    reread=SampleLedger(tmp_path)
    assert [r['stable_id'] for r in reread.accepted()]==['good']
    assert len(reread.history())==2
    assert reread.history()[0]['reason']=='Page anchor missing'


def test_bad_amendment_does_not_erase_previously_accepted_revision(tmp_path):
    ledger=SampleLedger(tmp_path);good={'reference':'Source-backed answer'}
    first=ledger.record('same_id',good,'accepted','Verified',proof(good['reference']))
    ledger.record('same_id',{'reference':'Unsupported amendment'},'quarantined','Invented claim')
    assert ledger.accepted()[0]['payload']==good
    assert ledger.history()[0]==first
    assert [r['revision'] for r in ledger.history()]==[1,2]


def test_modified_answer_requires_new_exact_review(tmp_path):
    ledger=SampleLedger(tmp_path)
    with pytest.raises(ValueError):
        ledger.record('changed',{'reference':'Different answer'},'accepted','Claimed unchanged',proof('Original answer'))


def test_proposal_survives_restart_before_source_validation(tmp_path):
    ledger=SampleLedger(tmp_path)
    proposal={'reference':'Pending answer','page':99,'query':'A retained proposal?'}
    ledger.record('pending',proposal,'proposed','Awaiting original source check')
    restarted=SampleLedger(tmp_path)
    assert restarted.history()[0]['payload']==proposal
    assert restarted.accepted()==[]
