"""Structural review controls: no assertion of a real model's answer quality."""
import copy
import hashlib
import pytest
from app.corrective_training import validate_manual_content_review


def test_review_cannot_approve_a_different_reference_or_source():
    h=lambda s:hashlib.sha256(s.encode()).hexdigest()
    m={'id':'s1','source_file_sha256':'a'*64,'passage':'native text','query':'question','reference':'reviewed answer'}
    c={'id':'s1','grade':'pass','source_verified':True,'reason':'source supports exact answer',
       'source_file_sha256':m['source_file_sha256'],'passage_sha256':h(m['passage']),
       'query_sha256':h(m['query']),'answer_sha256':h(m['reference'])}
    r={'reviewer':'Codex','content_review_complete':True,'dataset_sha256':'d','manifest_sha256':'m','cases':[c]}
    validate_manual_content_review([m],r,'d','m')
    for key,value in [('reference','unreviewed answer'),('passage','different source'),('query','new question'),('source_file_sha256','b'*64)]:
        changed=copy.deepcopy(m);changed[key]=value
        with pytest.raises(ValueError):validate_manual_content_review([changed],r,'d','m')
    for bad in [[],[c,c]]:
        changed=copy.deepcopy(r);changed['cases']=bad
        with pytest.raises(ValueError):validate_manual_content_review([m],changed,'d','m')
