"""A distinctive suffix must reach the embedder; long math/code must not vanish."""
import numpy as np
from app.indexer import KnowledgeIndexer, unpack_vector
from app.chunker import TextChunker

def indexer_with_document(tmp_path):
    indexer = KnowledgeIndexer(tmp_path/'index.db', tmp_path)
    with indexer.get_connection() as conn:
        conn.execute("INSERT INTO documents(id,filename,clean_title,filepath,file_size,file_hash,total_pages,extracted_pages_count,status) VALUES(1,'notes.pdf','Notes','notes.pdf',1,'sha',1,1,'indexed')")
    return indexer

def chunks(text):
    return [dict(book_title='Notes',filename='notes.pdf',page_num=1,chunk_index=0,text=text)]

def fake_embeddings(indexer, monkeypatch):
    calls=[]
    monkeypatch.setattr(indexer.ollama,'find_best_embed_model',lambda _: 'bge-m3:latest')
    monkeypatch.setattr(indexer.ollama,'get_embedding',lambda *a,**k:[1.,2.,3.])
    def embed(texts, **kwargs):
        calls.extend(texts)
        return [[float(len(t)),float('TAIL_SENTINEL' in t),3.] for t in texts]
    monkeypatch.setattr(indexer.ollama,'get_batch_embeddings',embed)
    return calls

def test_new_chunks_embed_distinctive_suffix(tmp_path, monkeypatch):
    indexer=indexer_with_document(tmp_path)
    calls=fake_embeddings(indexer,monkeypatch)
    text='a'*1100+' TAIL_SENTINEL'
    indexer._save_chunks(1,chunks(text),True,'bge-m3:latest')
    assert calls == [text]
    with indexer.get_connection() as conn:
        vec=unpack_vector(conn.execute('SELECT embedding FROM chunks').fetchone()[0])
    assert vec[1] == 1

def test_backfill_embeds_distinctive_suffix(tmp_path, monkeypatch):
    indexer=indexer_with_document(tmp_path)
    calls=fake_embeddings(indexer,monkeypatch)
    text='a'*1100+' TAIL_SENTINEL'
    indexer._save_chunks(1,chunks(text))
    assert indexer.backfill_missing_embeddings() == 1
    assert calls == [text]

def test_long_formula_chunks_are_bounded_and_cover_every_character():
    text=''.join(chr(0x4e00+i) for i in range(2500))+' TAIL_SENTINEL'
    result=TextChunker.chunk_page('Notes','notes.pdf',1,text,chunk_size=1200,chunk_overlap=100)
    assert all(len(c['text'])<=1200 for c in result)
    assert len(result)>1
    rebuilt=result[0]['text']
    for c in result[1:]:
        assert rebuilt[-100:]==c['text'][:100]
        rebuilt+=c['text'][100:]
    assert rebuilt==text

def test_embedding_batch_disables_server_truncation(monkeypatch):
    from app.ollama_client import OllamaClient
    payloads=[]
    class Response:
        status_code=200
        def raise_for_status(self): pass
        def json(self):return {'embeddings':[[1.,2.]]}
    def post(*a,**kwargs):payloads.append(kwargs['json']);return Response()
    monkeypatch.setattr('app.ollama_client.requests.post',post)
    assert OllamaClient().get_batch_embeddings(['full text'])==[[1.,2.]]
    assert payloads[0]['truncate'] is False
