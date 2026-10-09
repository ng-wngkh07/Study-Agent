import re
from typing import List, Dict, Any
from app.config import CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS

class TextChunker:
    @staticmethod
    def chunk_page(
        book_title: str,
        filename: str,
        page_num: int,
        page_text: str,
        chunk_size: int = CHUNK_SIZE_CHARS,
        chunk_overlap: int = CHUNK_OVERLAP_CHARS
    ) -> List[Dict[str, Any]]:
        """
        Split a page into manageable chunks with overlap while preserving book title and page number.
        If the page fits in chunk_size, keeps it as a single chunk.
        """
        text = page_text.strip()
        if not text:
            return []
        
        if chunk_size < 1 or not 0 <= chunk_overlap < chunk_size:
            raise ValueError("Require chunk_size > chunk_overlap >= 0")
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                # Prefer a paragraph, sentence, or word boundary. If none
                # exists, split long formulas/code without dropping characters.
                minimum = start + max(chunk_overlap + 1, chunk_size // 2)
                boundaries = list(re.finditer(r"\n\n|[.!?。]\s+|\s+", text[minimum:end]))
                if boundaries:
                    end = minimum + boundaries[-1].end()
            chunk_text = text[start:end]
            chunks.append({
                "book_title": book_title, "filename": filename,
                "page_num": page_num, "chunk_index": len(chunks),
                "text": chunk_text, "char_count": len(chunk_text),
                "char_start": start, "char_end": end,
            })
            if end == len(text):
                break
            start = end - chunk_overlap
        return chunks
