from app.dataset_balance import DOMAINS, assess_exposure


def records():
    return [dict(id=f'{split}-{domain}-{n}', split=split, domain=domain,
        source_file_sha256=f'{domain}-{n}') for split in ('train','valid')
        for domain in DOMAINS for n in range(2)]


def test_balanced_counts_sources_and_target_tokens_pass():
    rows = records()
    report = assess_exposure(rows, {r['id']:30 for r in rows})
    assert report['passed'] and report['exact_token_exposure_measured']


def test_combined_programming_aliases_cannot_hide_domain_dominance():
    rows = records()
    for n, alias in enumerate(['cpp','oop','algorithms','data_structures']):
        rows.append(dict(id=f'extra-{n}', split='train', domain=alias, source_file_sha256=f'extra-{n}'))
    report = assess_exposure(rows)
    assert not report['passed']
    assert 'train_unbalanced:programming' in report['failures']


def test_equal_sample_counts_do_not_hide_token_or_book_concentration():
    rows = records()
    lengths = {r['id']:300 if r['domain']=='psychology' else 10 for r in rows}
    assert 'target_token_exposure:psychology' in assess_exposure(rows,lengths)['failures']
    for row in rows:
        if row['domain']=='physics': row['source_file_sha256']='same-book'
    assert 'source_concentration:physics' in assess_exposure(rows)['failures']
def test_training_title_alone_cannot_replace_source_passage(tmp_path, monkeypatch):
    import json, sys, types, pytest
    from app.dataset_balance import exact_balance
    class Tokenizer:
        def encode(self,text,**kwargs): return list(text.split())
    monkeypatch.setitem(sys.modules,'transformers',types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a,**k:Tokenizer())))
    record={'id':'content-case','domain':'calculus','split':'train','source_file_sha256':'source-group',
        'passage':'The measured value is 17, under dry conditions.', 'reference':'The value is 17 [S1].'}
    title_only={'messages':[{'role':'system','content':'Answer based on sources'},
        {'role':'user','content':'According to Experimental Physics, what is the value?'},
        {'role':'assistant','content':record['reference']}]}
    (tmp_path/'approved_manifest.jsonl').write_text(json.dumps(record)+'\n')
    (tmp_path/'train.jsonl').write_text(json.dumps(title_only)+'\n')
    (tmp_path/'valid.jsonl').write_text('')
    with pytest.raises(ValueError,match='source passage'):
        exact_balance(tmp_path,tmp_path)
    grounded={'messages':[{'role':'system','content':'Answer based on sources'},
        {'role':'user','content':'[S1] '+record['passage']+'\nWhat is the value?'},
        {'role':'assistant','content':record['reference']}]}
    (tmp_path/'train.jsonl').write_text(json.dumps(grounded)+'\n')
    assert exact_balance(tmp_path,tmp_path)['source_context_bound'] is True
