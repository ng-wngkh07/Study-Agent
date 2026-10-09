import pytest
from pathlib import Path
from app.config import SRC_DIR
from app.pdf_extractor import PDFExtractor, PDFExtractionResult
from app.chunker import TextChunker

def test_src_directory_exists_and_has_pdfs():
    assert SRC_DIR.exists(), "src/ directory must exist"
    pdf_files = list(SRC_DIR.glob("*.pdf"))
    assert pdf_files, "src/ must contain at least one PDF"

def test_pdf_extraction_digital_text():
    # Test on a known digital text PDF
    sample_pdf = SRC_DIR / "5600-tu-duy-nhanh-va-cham-pdf-khoahoctamlinh.vn.pdf"
    assert sample_pdf.exists()
    
    res = PDFExtractor.extract_pdf(sample_pdf)
    assert res.error_message is None
    assert res.total_pages == 474
    assert res.is_scanned is False
    assert res.total_chars > 500000
    assert len(res.extracted_pages) == 474

def test_pdf_extraction_scanned_detection():
    # Test on scanned PDFs with 0 digital text
    scanned_pdf = SRC_DIR / "phaitraidungsai.pdf"
    assert scanned_pdf.exists()
    
    res = PDFExtractor.extract_pdf(scanned_pdf)
    assert res.total_pages == 245
    assert res.is_scanned is True
    assert res.total_chars == 0

def test_text_chunking():
    sample_text = (
        "Hệ thống 1 hoạt động tự động và nhanh chóng, với rất ít hoặc không có nỗ lực và không có sự tự chủ. "
        "Hệ thống 2 tập trung sự chú ý vào các hoạt động đòi hỏi nỗ lực trí óc, bao gồm các tính toán phức tạp."
    )
    chunks = TextChunker.chunk_page(
        book_title="Tư duy nhanh và chậm",
        filename="test.pdf",
        page_num=10,
        page_text=sample_text,
        chunk_size=1000
    )
    assert len(chunks) == 1
    assert chunks[0]["page_num"] == 10
    assert chunks[0]["book_title"] == "Tư duy nhanh và chậm"
    assert "Hệ thống 1" in chunks[0]["text"]
