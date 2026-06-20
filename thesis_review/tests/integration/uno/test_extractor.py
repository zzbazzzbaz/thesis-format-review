"""extractor 测试：UNO 读属性 → DocumentModel。"""
from __future__ import annotations

import pytest
from docx import Document

pytest.importorskip("uno")

from thesis_review.adapters.uno.extractor import extract
from thesis_review.adapters.uno.session import UnoSession


@pytest.mark.uno
def test_extract_paragraphs_from_sample(sample_docx):
    """至少抽出 5 段，含预期文本。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    assert model.source_docx == sample_docx
    paragraphs = [b for b in model.blocks if b.kind == "paragraph"]
    assert len(paragraphs) >= 5
    texts = [p.text for p in paragraphs]
    assert any("第一章" in t for t in texts)


@pytest.mark.uno
def test_extract_run_font_info(sample_docx):
    """可见文本 run 应读出字体和字号。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    text_paras = [
        p for p in model.blocks
        if p.kind == "paragraph" and p.text.strip() and p.runs
    ]
    run = text_paras[0].runs[0]
    assert run.font_east_asian
    assert run.size_pt is not None
    assert run.size_pt > 0


@pytest.mark.uno
def test_extract_block_and_run_ids_are_sequential(sample_docx):
    """块与 run 的 id 与索引一致。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    for block in model.blocks:
        assert block.id == f"b-{block.flow_index:04d}"
        if block.kind == "paragraph":
            for r in block.runs:
                assert r.id == f"{block.id}-r-{r.run_index:04d}"


@pytest.mark.uno
def test_extract_outline_level_for_heading(sample_docx):
    """一级标题 outline_level 应为 0（UNO 的 1 减 1）。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    headings = [
        p for p in model.blocks
        if p.kind == "paragraph" and p.outline_level is not None
    ]
    assert any(p.outline_level == 0 for p in headings), "一级标题 outline_level 应为 0"


@pytest.mark.uno
def test_extract_line_spacing_1_5(sample_docx):
    """规则样本中应能读出 1.5 倍行距。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    paragraphs = [
        p for p in model.blocks
        if p.kind == "paragraph" and p.outline_level is None and p.text
    ]
    assert any(
        p.line_spacing == pytest.approx(1.5, abs=0.01)
        for p in paragraphs
    )


@pytest.mark.uno
def test_extract_style_name(sample_docx):
    """标题段落应读出样式名 Heading 1。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    heading = next(
        p for p in model.blocks
        if p.kind == "paragraph" and p.outline_level is not None
    )
    assert heading.style_name == "Heading 1"


@pytest.mark.uno
def test_extract_handles_rule_sample_docx(sample_docx):
    """规则样本至少能抽出段落文本。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    paragraphs = [b for b in model.blocks if b.kind == "paragraph"]
    assert len(paragraphs) >= 1
    assert any(p.text for p in paragraphs)


@pytest.mark.uno
def test_extract_preserves_empty_paragraphs(tmp_path):
    """空段落应保留在文档流中，用于判断目录标题后空一行。"""
    path = tmp_path / "with_empty.docx"
    docx = Document()
    docx.add_paragraph("目    录")
    docx.add_paragraph("")
    docx.add_paragraph("第一章  引言\t1")
    docx.save(path)

    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))

    paragraphs = [block for block in model.blocks if block.kind == "paragraph"]
    assert [p.text for p in paragraphs] == ["目    录", "", "第一章  引言\t1"]
    assert paragraphs[1].is_empty is True
    assert paragraphs[1].runs == []
    assert [p.flow_index for p in paragraphs] == [0, 1, 2]


@pytest.mark.uno
def test_extract_superscript_run(tmp_path):
    """正文引用上标应抽取为 RunSpan.superscript=True。"""
    path = tmp_path / "with_superscript.docx"
    docx = Document()
    paragraph = docx.add_paragraph()
    paragraph.add_run("正文引用")
    cite = paragraph.add_run("[1]")
    cite.font.superscript = True
    docx.save(path)

    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))

    para = next(
        block for block in model.blocks
        if block.kind == "paragraph" and "[1]" in block.text
    )
    cite_run = next(run for run in para.runs if "[1]" in run.text)
    assert cite_run.superscript is True


@pytest.mark.uno
def test_extract_alignment_default_left(sample_docx):
    """规则样本中应能读出左对齐段落。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    body_paras = [
        p for p in model.blocks
        if p.kind == "paragraph" and p.outline_level is None
    ]
    assert any(p.alignment == "left" for p in body_paras)


@pytest.mark.uno
def test_extract_first_line_indent_zero_when_not_set(sample_docx):
    """规则样本第四段无首行缩进，first_line_indent_chars = 0。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
    paragraphs = [b for b in model.blocks if b.kind == "paragraph"]
    p4 = paragraphs[4]
    assert p4.first_line_indent_chars == 0.0


@pytest.mark.uno
def test_extract_preserves_table_in_flow(tmp_path):
    """表格应作为独立 block 保留在段落之间的文档流位置。"""
    path = tmp_path / "with_table.docx"
    docx = Document()
    docx.add_paragraph("表前段落")
    table = docx.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "A1"
    table.cell(0, 1).text = "A2"
    table.cell(1, 0).text = "B1"
    table.cell(1, 1).text = "B2"
    docx.add_paragraph("表后段落")
    docx.save(path)

    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))

    assert [block.kind for block in model.blocks] == ["paragraph", "table", "paragraph"]
    assert model.blocks[0].flow_index == 0
    assert model.blocks[1].flow_index == 1
    assert model.blocks[2].flow_index == 2
    assert model.blocks[0].type_index == 0
    assert model.blocks[1].type_index == 0
    assert model.blocks[2].type_index == 1
    table_block = model.blocks[1]
    assert table_block.row_count == 2
    assert table_block.column_count == 2
    assert "A1" in table_block.text
    assert "B2" in table_block.text
