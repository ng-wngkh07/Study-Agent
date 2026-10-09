"""Metrics for held-out answers, independent of the MLX runtime."""

import re
from collections import Counter


def has_language_drift(answer: str) -> bool:
    """Flag substantial Han-script output in the Vietnamese-only answer flow."""
    han = len(re.findall(r"[\u3400-\u9fff]", answer))
    letters = sum(character.isalpha() for character in answer)
    return han >= 10 and han / max(letters, 1) >= 0.05


def has_repetition(answer: str) -> bool:
    """Detect substantial sentences repeated three or more times."""
    text = re.sub(r"\[S\d+\]", "", answer, flags=re.I)
    sentences = [" ".join(s.casefold().split()) for s in re.split(r"[.!?\n]+", text)]
    substantial = [s for s in sentences if len(s.split()) >= 8]
    return any(count >= 3 for count in Counter(substantial).values())


def citation_metrics(answer: str, source_ids: set[str]) -> dict:
    """Require every provided source and reject citations to unknown sources."""
    cited = set(re.findall(r"\[(S\d+)\]", answer))
    return {
        "cited_sources": sorted(cited),
        "citation_tags_valid": bool(cited) and cited.issubset(source_ids),
        "citation_valid": bool(source_ids) and cited == source_ids,
    }


def plain_answer_metrics(answer: str) -> dict:
    """Check only visible format; factual accuracy still needs source review."""
    forbidden = re.search(
        r"(?i)<\s*(?:think|analysis|reasoning)\b|\[S\d+\]|\[[^\]\n]+,\s*Trang\s+\d+\]|"
        r"(?m:^\s*(?:Nguồn(?: tham khảo)?|Trích dẫn|Câu trả lời(?: cuối cùng)?|Giải thích suy luận)\s*:)",
        answer,
    )
    return {"format_valid": bool(answer.strip()) and forbidden is None,
            "repetitive": has_repetition(answer),
            "has_visible_citations": bool(re.search(r"\[S\d+\]|\[[^\]\n]+,\s*Trang\s+\d+\]", answer, re.I))}
