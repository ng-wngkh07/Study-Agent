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
