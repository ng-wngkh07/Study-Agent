import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_three_learning_tabs_share_one_tools_navigation_item():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    nav = re.search(r'<nav class="mode-switch"[^>]*>(.*?)</nav>', html, re.S).group(1)
    assert 'id="mode-tools"' in nav
    assert 'id="mode-documents"' not in nav
    assert nav.count('id="mode-tools"') == 1

    tools = re.search(
        r'<section id="learning-tools-panel".*?</section>\s*</section>\s*<section id="timetable-panel"',
        html,
        re.S,
    ).group(0)
    for tab in ("practice", "review", "examples"):
        assert f'id="btn-tool-tab-{tab}"' in tools
        assert f'id="tool-tab-{tab}"' in tools
    assert re.findall(r'role="tab"[^>]*>(.*?)</button>', tools) == [
        "Tạo câu hỏi",
        'Ôn tập <span id="review-count">0</span>',
        "Trích xuất bài tập mẫu",
    ]
    assert 'id="tool-tab-practice"' in tools
    assert 'id="tool-tab-review"' in tools
    assert 'id="tool-tab-examples"' in tools
    assert "Câu hỏi do AI tạo" in tools
    assert "nội dung không được AI viết lại" in tools
    assert "localStorage" in tools or "trình duyệt này" in tools
    assert "Xóa toàn bộ tiến độ" in tools


def test_learning_tools_have_theme_rules_and_no_decorative_images_or_gradients():
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8").lower()
    assert "prefers-color-scheme: dark" in css
    assert "background-image" not in css
    assert "gradient(" not in css
