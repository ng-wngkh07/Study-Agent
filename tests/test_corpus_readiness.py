import hashlib
import json
import pytest
from app.indexer import KnowledgeIndexer, pack_vector
from app.corpus_readiness import audit_corpus


@pytest.fixture
def corpus(tmp_path):
    src = tmp_path/'src'; src.mkdir()
    (src/'note.txt').write_text('All 17 source items remain scoped to this one question. Tail sentinel.', encoding='utf-8')
    data = tmp_path/'data'; data.mkdir()
    idx = KnowledgeIndexer(data/'knowledge_base.db', src)
    idx.index_all(embed_model=None)
    runtime = data/'runtime'; runtime.mkdir()
    (runtime/'corpus_completion_policy.json').write_text(json.dumps({'require_complete_corpus':True,'embedding_model_digest':'pinned-bge'}))
    with idx.get_connection() as db:
        db.execute('CREATE TABLE corpus_source_pages(filename,page_num,source_sha256,state,chunks_sha256,review_path,review_sha256,checked_at)')
        db.execute('CREATE TABLE corpus_vector_provenance(chunk_id,text_sha256,model_digest,vector_sha256,dimensions,full_text,embedded_at)')
        texts = [r['text'] for r in db.execute('SELECT text FROM chunks ORDER BY chunk_index')]
        db.execute('INSERT INTO corpus_source_pages VALUES(?,?,?,?,?,?,?,?)', ('note.txt',1,hashlib.sha256((src/'note.txt').read_bytes()).hexdigest(),'text_verified',hashlib.sha256(json.dumps(texts,ensure_ascii=False).encode()).hexdigest(),'','','now'))
        for r in db.execute('SELECT id,text FROM chunks').fetchall():
            blob = pack_vector([1.]+[0.]*1023)
            db.execute('UPDATE chunks SET embedding=? WHERE id=?',(blob,r['id']))
            db.execute('INSERT INTO corpus_vector_provenance VALUES(?,?,?,?,?,?,?)', (r['id'],hashlib.sha256(r['text'].encode()).hexdigest(),'pinned-bge',hashlib.sha256(blob).hexdigest(),1024,1,'now'))
    return tmp_path, idx


def test_current_complete_corpus_passes(corpus):
    root, _ = corpus
    assert audit_corpus(root)['complete']


@pytest.mark.parametrize('fault', ['missing_vector','nan_vector','zero_vector','truncated_proof','changed_chunk','source_changed','new_document','partial_page','unsupported_file'])
def test_training_readiness_rejects_real_missing_or_stale_inputs(corpus, fault):
    root, idx = corpus
    if fault=='source_changed': (root/'src/note.txt').write_text('Changed source')
    elif fault=='new_document': (root/'src/new.txt').write_text('Entire additional source absent from index.')
    elif fault=='unsupported_file': (root/'src/new.xyz').write_text('Unsupported document')
    else:
        with idx.get_connection() as db:
            if fault=='missing_vector': db.execute('UPDATE chunks SET embedding=NULL')
            elif fault=='nan_vector': db.execute('UPDATE chunks SET embedding=?',(pack_vector([float('nan')]*1024),))
            elif fault=='zero_vector': db.execute('UPDATE chunks SET embedding=?',(pack_vector([0.]*1024),))
            elif fault=='truncated_proof': db.execute('UPDATE corpus_vector_provenance SET full_text=0')
            elif fault=='changed_chunk': db.execute("UPDATE chunks SET text=text || ' invented tail'")
            elif fault=='partial_page': db.execute("UPDATE corpus_source_pages SET state='handwriting_partial'")
    report = audit_corpus(root)
    assert not report['complete'] and report['failures']


def approved_page_scope(root, *, partial=True):
    """A human-approved single-page exception; keeps source and DB untouched."""
    import sqlite3
    runtime = root / 'data/runtime'
    image = runtime / 'source-image.png'
    image.write_bytes(b'fixture source image')
    manifest = {
        'schema': 'approved-page-exclusions-v1', 'decision_id': 'YC-188',
        'approved_by': 'user', 'approved_at': '2026-10-10T17:40:00+07:00',
        'approval': 'EXCLUDE_PREVIOUSLY_REVIEWED_UNRESOLVED_PAGES',
        'approved_count': 1,
        'pages': [{'filename': 'note.txt', 'page': 1,
                   'source_sha256': hashlib.sha256((root/'src/note.txt').read_bytes()).hexdigest(),
                   'image_path': str(image), 'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                   'reason': ['Original content is clipped; user approved exclusion.']}],
    }
    path = runtime / 'approved-exclusions.json'
    path.write_text(json.dumps(manifest))
    policy_path = runtime/'corpus_completion_policy.json'
    policy = json.loads(policy_path.read_text())
    policy['page_exclusion_manifest'] = {'path': 'data/runtime/approved-exclusions.json',
                                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    policy_path.write_text(json.dumps(policy))
    if partial:
        with sqlite3.connect(root/'data/knowledge_base.db') as db:
            db.execute("UPDATE corpus_source_pages SET state='ocr_pending_review'")
    return path, manifest, policy_path, policy


def test_approved_exception_reports_scope_and_never_fakes_whole_source_completion(corpus):
    root, idx = corpus
    approved_page_scope(root)
    result = audit_corpus(root)
    assert result['complete'], result['failures']
    assert result['complete_all_sources'] is False
    assert result['excluded_page_count'] == 1 and result['in_scope_pages'] == 0
    with idx.get_connection() as db:
        assert db.execute('SELECT state FROM corpus_source_pages').fetchone()[0] == 'ocr_pending_review'
        assert db.execute('SELECT COUNT(*) FROM chunks').fetchone()[0] > 0


@pytest.mark.parametrize('fault', ['manifest_tampered', 'source_hash', 'image_hash', 'unauthorized',
                                   'duplicate', 'wildcard', 'out_of_range', 'outside_root',
                                   'missing_approval_time', 'missing_reason', 'manifest_symlink'])
def test_exclusion_cannot_silently_expand_or_use_stale_approval(corpus, fault):
    root, _ = corpus
    path, manifest, policy_path, policy = approved_page_scope(root, partial=False)
    if fault == 'manifest_tampered':
        path.write_text(path.read_text() + ' ')
    elif fault == 'manifest_symlink':
        alias = path.parent/'alias.json'
        alias.symlink_to(path)
        policy['page_exclusion_manifest']['path'] = str(alias.relative_to(root))
        policy_path.write_text(json.dumps(policy))
    elif fault == 'outside_root':
        policy['page_exclusion_manifest']['path'] = '../outside.json'
        policy_path.write_text(json.dumps(policy))
    else:
        page = manifest['pages'][0]
        if fault == 'source_hash': page['source_sha256'] = '0'*64
        elif fault == 'image_hash': page['image_sha256'] = '0'*64
        elif fault == 'unauthorized': manifest['approved_by'] = 'automatic_ocr'
        elif fault == 'missing_approval_time': manifest.pop('approved_at')
        elif fault == 'missing_reason': page.pop('reason')
        elif fault == 'duplicate': manifest['pages'].append(dict(page)); manifest['approved_count'] = 2
        elif fault == 'wildcard': page['filename'] = '*'
        elif fault == 'out_of_range': page['page'] = 2
        path.write_text(json.dumps(manifest))
        policy['page_exclusion_manifest']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        policy_path.write_text(json.dumps(policy))
    result = audit_corpus(root)
    assert not result['complete'], fault
    assert result['failures']


@pytest.mark.parametrize('fault', ['vector', 'chunk', 'source'])
def test_exception_preserves_non_content_integrity_checks(corpus, fault):
    root, idx = corpus
    approved_page_scope(root)
    if fault == 'source':
        (root/'src/note.txt').write_text('The original source has changed.')
    else:
        with idx.get_connection() as db:
            if fault == 'vector': db.execute('UPDATE chunks SET embedding=NULL')
            else: db.execute("UPDATE chunks SET text=text || ' tampered'")
    assert not audit_corpus(root)['complete']


@pytest.mark.parametrize('layout', ['top_level', 'pair_sources'])
def test_consumer_rejects_excluded_sources_in_actual_split_files(corpus, layout):
    from app.corpus_scope import verify_dataset_scope
    root, _ = corpus
    approved_page_scope(root)
    data_dir = root/'candidate'; data_dir.mkdir()
    (data_dir/'approved_manifest.jsonl').write_text('')
    item = {'source_file':'note.txt', 'page':1} if layout == 'top_level' else {
        'pair': {'filename':'note.txt', 'sources':[{'page':1}]}}
    (data_dir/'train.jsonl').write_text(json.dumps(item)+'\n')
    with pytest.raises(ValueError):
        verify_dataset_scope(data_dir, root=root)


def test_consumer_rejects_manifest_with_no_source_page_provenance(corpus):
    from app.corpus_scope import verify_dataset_scope
    root, _ = corpus
    approved_page_scope(root)
    data_dir = root/'candidate'; data_dir.mkdir()
    (data_dir/'approved_manifest.jsonl').write_text(json.dumps({'id':'row1','split':'train'})+'\n')
    with pytest.raises(ValueError):
        verify_dataset_scope(data_dir, root=root)


def test_corrupt_scope_policy_does_not_admit_native_training_text(corpus, monkeypatch):
    from app import config, training_data
    root, idx = corpus
    approved_page_scope(root)
    (root/'data/runtime/corpus_completion_policy.json').write_text('{broken')
    monkeypatch.setattr(config, 'BASE_DIR', root)
    monkeypatch.setattr(config, 'SRC_DIR', root/'src')
    with idx.get_connection() as db:
        doc = db.execute('SELECT * FROM documents').fetchone()
        text = db.execute('SELECT text FROM chunks').fetchone()[0]
    assert training_data.is_chunk_allowed_in_training(doc, 1, text) is False


@pytest.mark.parametrize('fault', ['alias', 'unknown_file', 'negative_page', 'fraction_page',
                                   'boolean_page', 'self_declared_control', 'missing_manifest',
                                   'malformed_raw_json', 'partial_raw_provenance'])
def test_scope_consumer_fails_closed_on_ambiguous_or_unknown_provenance(corpus, fault):
    from app.corpus_scope import verify_dataset_scope
    root, _ = corpus
    approved_page_scope(root)
    data_dir = root/'candidate'; data_dir.mkdir()
    item = {'source_file':'note.txt', 'page':1}
    if fault == 'alias': item['source_file'] = './note.txt'
    elif fault == 'unknown_file': item['source_file'] = 'invented.txt'
    elif fault == 'negative_page': item['page'] = -1
    elif fault == 'fraction_page': item['page'] = 0.5
    elif fault == 'boolean_page': item['page'] = False
    elif fault == 'self_declared_control': item = {'control_fixture':True}
    if fault != 'missing_manifest':
        (data_dir/'approved_manifest.jsonl').write_text(json.dumps(item)+'\n')
    if fault == 'malformed_raw_json': (data_dir/'train.jsonl').write_text('{broken\n')
    elif fault == 'partial_raw_provenance':
        (data_dir/'train.jsonl').write_text(json.dumps({'source_file':'note.txt'})+'\n')
    else: (data_dir/'train.jsonl').write_text(json.dumps({'messages':[]})+'\n')
    with pytest.raises(ValueError):
        verify_dataset_scope(data_dir, root=root)


@pytest.mark.parametrize('raw', ['{broken', '[]', '{"source_file":"allowed.txt"}',
                                '{"sources":[{"filename":"./note.txt","page":1}]}'])
def test_scope_checks_actual_rows_after_a_valid_manifest(corpus, raw):
    from app.corpus_scope import verify_dataset_scope
    root, _ = corpus
    approved_page_scope(root)
    (root/'src/allowed.txt').write_text('An independent admitted source passage with a complete sentence.')
    data_dir = root/'candidate'; data_dir.mkdir()
    row = {'id':'row1','split':'train','source_file':'allowed.txt','page':1}
    (data_dir/'approved_manifest.jsonl').write_text(json.dumps(row)+'\n')
    (data_dir/'train.jsonl').write_text(raw+'\n')
    with pytest.raises(ValueError):
        verify_dataset_scope(data_dir, root=root)


def test_scope_allows_message_only_rows_bound_to_valid_manifest(corpus):
    from app.corpus_scope import verify_dataset_scope
    root, _ = corpus
    approved_page_scope(root)
    (root/'src/allowed.txt').write_text('An independent admitted source passage with a complete sentence.')
    data_dir = root/'candidate'; data_dir.mkdir()
    row = {'id':'row1','split':'train','source_file':'allowed.txt','page':1}
    (data_dir/'approved_manifest.jsonl').write_text(json.dumps(row)+'\n')
    (data_dir/'train.jsonl').write_text(json.dumps({'messages':[{'role':'user','content':'Question'},
        {'role':'assistant','content':'Answer'}]})+'\n')
    verify_dataset_scope(data_dir, root=root)
