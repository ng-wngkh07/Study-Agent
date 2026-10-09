import pymupdf

from app.pdf_extractor import PDFExtractor


def test_force_ocr_replaces_corrupt_digital_text(tmp_path, monkeypatch):
    pdf_path = tmp_path / "legacy.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "This digital text is deliberately wrong and should not be indexed.")
    document.save(pdf_path)
    document.close()

    monkeypatch.setattr(PDFExtractor, "ocr_available", staticmethod(lambda: True))
    monkeypatch.setattr(
        PDFExtractor, "_ocr_page",
        staticmethod(lambda page, file_hash, page_num: "Văn bản tiếng Việt được nhận dạng chính xác từ hình ảnh của trang."),
    )

    result = PDFExtractor.extract_pdf(pdf_path, force_ocr=True)
    assert result.ocr_pages == 1
    assert "Văn bản tiếng Việt" in result.extracted_pages[0]["text"]
    assert "deliberately wrong" not in result.extracted_pages[0]["text"]
