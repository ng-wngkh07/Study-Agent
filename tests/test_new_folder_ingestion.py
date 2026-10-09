import zipfile
from app.pdf_extractor import PDFExtractor
from app.document_lookup import DocumentLookup
from app.indexer import KnowledgeIndexer


def test_powerpoint_preserves_presentation_order_tables_and_notes(tmp_path):
    path = tmp_path / 'notes.pptx'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('ppt/presentation.xml', '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="r2"/><p:sldId id="257" r:id="r1"/></p:sldIdLst></p:presentation>')
        z.writestr('ppt/_rels/presentation.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Target="slides/slide1.xml"/><Relationship Id="r2" Target="slides/slide2.xml"/></Relationships>')
        for n, text in [(1, 'SECOND slide'), (2, 'FIRST slide. array[1][2] = 17;')]:
            z.writestr(f'ppt/slides/slide{n}.xml', f'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:p><a:r><a:t>{text}</a:t></a:r></a:p><a:tbl><a:p><a:r><a:t>table cell sentinel</a:t></a:r></a:p></a:tbl></p:sld>')
        z.writestr('ppt/slides/_rels/slide2.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="note" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide2.xml"/></Relationships>')
        z.writestr('ppt/notesSlides/notesSlide2.xml', '<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:r><a:t>notes sentinel</a:t></a:r></a:p>')
    assert path in PDFExtractor.discover_source_files(tmp_path)['supported']
    result = PDFExtractor.extract_file(path)
    assert result.error_message is None
    assert result.total_pages == 2
    assert 'FIRST slide' in result.extracted_pages[0]['text']
    assert 'array[1][2] = 17;' in result.extracted_pages[0]['text']
    assert 'table cell sentinel' in result.extracted_pages[0]['text']
    assert 'notes sentinel' in result.extracted_pages[0]['text']
    assert result.extracted_pages[0]['unit_type'] == 'slide'
    assert 'SECOND slide' in result.extracted_pages[1]['text']
    idx = KnowledgeIndexer(tmp_path/'index.db', tmp_path)
    idx.index_all(embed_model=None)
    assert DocumentLookup(tmp_path/'index.db', tmp_path).documents()[0]['filename'] == 'notes.pptx'
    from app.training_data import is_chunk_allowed_in_training
    with idx.get_connection() as db:
        doc = db.execute('SELECT * FROM documents').fetchone()
        text = db.execute('SELECT text FROM chunks WHERE page_num=1').fetchone()[0]
    assert is_chunk_allowed_in_training(doc, 1, text)
    assert not is_chunk_allowed_in_training(doc, 1, text+' invented unsupported tail')


def test_index_embedding_backfill_reports_progress_after_unchanged_document(tmp_path, monkeypatch):
    (tmp_path/'note.txt').write_text('A sufficiently long paragraph with a distinctive final sentinel.', encoding='utf-8')
    idx = KnowledgeIndexer(tmp_path/'index.db', tmp_path)
    idx.index_all(embed_model=None)
    monkeypatch.setattr(idx.ollama, 'find_best_embed_model', lambda _: 'bge-m3')
    monkeypatch.setattr(idx.ollama, 'get_embedding', lambda *a, **k: [1., 2.])
    monkeypatch.setattr(idx.ollama, 'get_batch_embeddings', lambda texts, **k: [[1., 2.] for _ in texts])
    progress = []
    result = idx.index_all(embed_model='bge-m3', progress_callback=lambda *args: progress.append(args))
    assert result['embeddings_backfilled'] == 1
    assert any('Embedding Backfill' in args for args in progress)
