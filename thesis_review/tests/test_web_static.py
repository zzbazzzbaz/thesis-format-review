"""静态上传页面结构测试。"""
from __future__ import annotations

from pathlib import Path


STATIC_DIR = Path(__file__).parents[1] / "src" / "thesis_review" / "web" / "static"


def test_index_has_docx_upload_form_and_fetch_logic():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert '<form id="review-form">' in html
    assert 'name="file"' in html
    assert 'accept=".docx"' in html
    assert 'fetch("/api/review"' in html
    assert "URL.createObjectURL" in html
    assert "正在审核" in html
    assert "审核失败" in html


def test_style_defines_upload_states():
    css = (STATIC_DIR / "style.css").read_text(encoding="utf-8")

    assert ".shell" in css
    assert "button:disabled" in css
    assert ".status.error" in css
    assert ".status.success" in css
