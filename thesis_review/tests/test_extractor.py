"""extractor 测试：UNO 读属性 → DocumentModel。"""
from __future__ import annotations

import pytest

from src.extractor import extract
from src.uno_session import UnoSession


@pytest.mark.uno
def test_extract_paragraphs_from_sample(sample_docx):
    """至少抽出 5 段，含预期文本。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    assert model.source_docx == sample_docx
    assert len(model.paragraphs) >= 5
    texts = [p.text for p in model.paragraphs]
    assert any("第一章" in t for t in texts)


@pytest.mark.uno
def test_extract_run_font_info(sample_docx):
    """正文第一段 run 应读出楷体 + 14pt。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    body_paras = [p for p in model.paragraphs if p.outline_level is None and p.runs]
    p1 = body_paras[0]
    assert len(p1.runs) >= 1
    assert p1.runs[0].font_east_asian == "楷体"
    assert p1.runs[0].size_pt == 14.0


@pytest.mark.uno
def test_extract_run_ids_are_sequential(sample_docx):
    """段落与 run 的 id 与索引一致。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    for p in model.paragraphs:
        assert p.id == f"p-{p.paragraph_index:04d}"
        for r in p.runs:
            assert r.id == f"{p.id}-r-{r.run_index:04d}"


@pytest.mark.uno
def test_extract_outline_level_for_heading(sample_docx):
    """一级标题 outline_level 应为 0（UNO 的 1 减 1）。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    headings = [p for p in model.paragraphs if p.outline_level is not None]
    assert any(p.outline_level == 0 for p in headings), "一级标题 outline_level 应为 0"


@pytest.mark.uno
def test_extract_line_spacing_1_5(sample_docx):
    """正文第一段行距应为 1.5 倍。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    body = [p for p in model.paragraphs if p.outline_level is None and p.text]
    assert body[0].line_spacing == pytest.approx(1.5, abs=0.01)


@pytest.mark.uno
def test_extract_style_name(sample_docx):
    """标题段落应读出样式名 Heading 1。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    heading = next(p for p in model.paragraphs if p.outline_level is not None)
    assert heading.style_name == "Heading 1"


@pytest.mark.uno
def test_extract_handles_wps_edited_docx(wps_docx):
    """WPS 手工编辑版至少能抽出段落文本。"""
    with UnoSession() as session:
        with session.open(wps_docx) as doc:
            model = extract(doc, source_path=wps_docx)
    assert len(model.paragraphs) >= 1
    assert any(p.text for p in model.paragraphs)


@pytest.mark.uno
def test_extract_no_empty_tail_paragraph(sample_docx):
    """所有段落应有非空文本（末尾空段被跳过）。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    for p in model.paragraphs:
        assert p.text.strip(), f"段落 {p.id} 不应为空"


@pytest.mark.uno
def test_extract_alignment_default_left(sample_docx):
    """正文段落默认左对齐。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    body_paras = [p for p in model.paragraphs if p.outline_level is None]
    assert body_paras[0].alignment == "left"


@pytest.mark.uno
def test_extract_first_line_indent_zero_when_not_set(sample_docx):
    """sample.docx 第四段无首行缩进，first_line_indent_chars = 0。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    p4 = model.paragraphs[4]
    assert p4.first_line_indent_chars == 0.0
