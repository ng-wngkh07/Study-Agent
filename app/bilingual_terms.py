"""Shared psychology terminology checks for runtime and training translations."""

import re


def translation_guidance(source: str = "") -> str:
    """Select relevant terms; shadowing speech is not Jung's shadow."""
    terms = {
        "shadow": "cái bóng (khía cạnh bị che giấu của nhân cách)",
        "projection": "sự phóng chiếu", "unconscious": "vô thức",
        "working memory": "trí nhớ làm việc", "phonological loop": "vòng lặp âm vị",
        "visuospatial sketchpad": "bảng phác họa thị giác-không gian",
        "central executive": "bộ điều hành trung tâm", "hippocampus": "hồi hải mã",
        "declarative memory": "trí nhớ khai báo", "semantic memory": "trí nhớ ngữ nghĩa",
        "gene": "gen", "allele": "alen", "dominant": "trội", "recessive": "lặn",
        "sexual reproduction": "sinh sản hữu tính",
    }
    value = source.casefold()
    selected = [f"{term} = {meaning}" for term, meaning in terms.items()
                if not source or re.search(r"\b" + re.escape(term) + r"\b", value)]
    if "shadowed" in value or "shadowing" in value:
        selected.append("shadowing speech = nghe và lặp lại lời nói; không phải cái bóng theo Jung")
    if "project information" in value:
        selected.append("project information = truyền/chuyển thông tin đến vùng khác")
    return ("Relevant terminology: " + "; ".join(selected) + ". " if selected else "") + "Preserve proper names and the meaning in context. "


def translation_is_plausible(source: str, translation: str) -> bool:
    value = translation.casefold()
    if len(translation.strip()) < max(30, 0.35 * len(source.strip())):
        return False
    # Runtime cache must enforce the same language boundary as training data.
    if re.search(r"[\u3400-\u9fff]", translation):
        return False
    if len(re.findall(r"[ăâđêôơưĂÂĐÊÔƠƯ\u1ea0-\u1ef9]", translation)) < max(3, len(translation) // 150):
        return False
    if any(phrase in value for phrase in ("tầm thân", "dự án bóng", "dự án của mình", "dự án mạnh mẽ",
                                           "sktech", "patronize", "hypnotic", "working memory")):
        return False
    if "projection" in source.casefold() and "dự án" in value:
        return False
    if "dominant" in source.casefold() and "bắc cầu" in value:
        return False
    if "sexual reproduction" in source.casefold() and "trải nghiệm sinh" in value:
        return False
    if any(marker in value for marker in ("trả lời:", "câu hỏi:", "[s1]", "[s2]", "<think>")):
        return False
    return True
