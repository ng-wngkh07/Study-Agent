"""Keep private reasoning and source markers out of the user-facing answer."""

import re


_THINK = re.compile(r"<\s*(?:think|analysis|reasoning)\b[^>]*>.*?<\s*/\s*(?:think|analysis|reasoning)\s*>", re.I | re.S)
_FINAL = re.compile(r"<\s*final\s*>(.*?)<\s*/\s*final\s*>", re.I | re.S)
_SOURCE = re.compile(r"\[\s*S\d+(?:\s*[,;]\s*S\d+)*\s*\]", re.I)
_BOOK_SOURCE = re.compile(r"\[[^\[\]\n]{2,160},\s*Trang\s+\d+\]", re.I)
_SOURCE_SECTION = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:nguồn(?: tham khảo)?|trích dẫn|tài liệu tham khảo|sources?|references?)\s*:\s*.*(?:\n(?:\s*[-*].*|\s*\[S\d+\].*)?)*$")


def clean_answer(text: str) -> str:
    text = _THINK.sub("", text)
    final = _FINAL.search(text)
    if final:
        text = final.group(1)
    text = re.sub(r"(?is)^.*?<\s*/\s*(?:think|analysis|reasoning)\s*>", "", text)
    text = re.sub(r"(?im)^\s*(?:#{1,6}\s*)?(?:câu trả lời(?: cuối cùng)?|final answer)\s*:\s*", "", text)
    text = re.sub(r"(?im)^\s*(?:[-*]\s*)?(?:nêu dữ kiện có nguồn|giải thích suy luận(?: rút ra từ các dữ kiện)?|mức độ chắc chắn|giới hạn(?: hoặc điểm chưa có chứng cứ)?|tóm lại)\s*:\s*", "", text)
    text = _SOURCE_SECTION.sub("", text)
    text = re.sub(r"(?i)\b(?:theo|trong|ở)\s+(?:đoạn|nguồn)\s*\[S\d+\]\s*,?\s*", "", text)
    text = _SOURCE.sub("", text)
    text = _BOOK_SOURCE.sub("", text)
    text = re.sub(r"\bTầm Thân\b", "cái bóng", text, flags=re.I)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text[:1].upper() + text[1:] if text else ""
