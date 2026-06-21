"""extractor 测试：UNO 读属性 → DocumentModel。"""
from __future__ import annotations

import pytest
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.shared import Cm, Pt

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


@pytest.mark.uno
def test_extract_page_style_header_footer_and_page_number(tmp_path):
    """页样式应包含页眉页脚文本，正文块应带页面样式名。"""
    path = tmp_path / "with_header_footer.docx"
    docx = Document()
    section = docx.sections[0]
    header_para = section.header.paragraphs[0]
    header_para.text = "山东石油化工学院本科毕业设计（论文）"
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_run = header_para.runs[0]
    header_run.font.name = "SimHei"
    header_run.font.size = Pt(10.5)
    footer_para = section.footer.paragraphs[0]
    footer_para.text = "1"
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_para.runs[0]
    footer_run.font.name = "Times New Roman"
    footer_run.font.size = Pt(10.5)
    docx.add_paragraph("摘    要")
    docx.add_paragraph("摘要正文")
    docx.add_paragraph("目    录")
    docx.add_paragraph("第一章  引言")
    docx.save(path)

    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))

    assert model.page_styles
    assert any(style.header_text for style in model.page_styles)
    assert any(style.footer_text for style in model.page_styles)
    assert any(block.page_style_name for block in model.blocks)


@pytest.mark.uno
def test_extract_uses_ooxml_page_number_size_when_uno_textfield_size_is_wrong():
    """页脚 PAGE 字段字号以 OOXML 字段结果 run 为准，避免 UNO 导入失真。"""
    path = "docs/rules/global/samples/global-header-format.docx"

    with UnoSession() as session:
        with session.open(path) as doc:
            model = extract(doc, source_path=path)

    page_number_runs = [
        run
        for style in model.page_styles
        for paragraph in style.footer_paragraphs
        if paragraph.page_number_text
        for run in paragraph.runs
        if run.text.strip().isdigit()
    ]
    assert page_number_runs
    assert {run.size_pt for run in page_number_runs} == {10.5}


@pytest.mark.uno
def test_extract_preserves_ooxml_page_number_size_violation_from_rule_sample():
    """真实页码字号错误样本应从 OOXML 抽出 12pt。"""
    path = "docs/rules/global/samples/global-footer-page-number-format.docx"

    with UnoSession() as session:
        with session.open(path) as doc:
            model = extract(doc, source_path=path)

    page_number_runs = [
        run
        for style in model.page_styles
        for paragraph in style.footer_paragraphs
        if paragraph.page_number_text
        for run in paragraph.runs
        if run.text.strip().isdigit()
    ]
    assert page_number_runs
    assert {run.size_pt for run in page_number_runs} == {12.0}


@pytest.mark.uno
def test_extract_preserves_image_in_flow(tmp_path):
    """正文图片应作为 ImageBlock 出现在图题前。"""
    path = tmp_path / "with_image.docx"
    image_path = tmp_path / "pixel.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xe2`"
        b"\x82\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    docx_file = Document()
    docx_file.add_paragraph("图前段落")
    docx_file.add_picture(str(image_path))
    docx_file.add_paragraph("图1-1 示例")
    docx_file.save(path)

    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))

    kinds = [block.kind for block in model.blocks]
    assert "image" in kinds
    assert kinds.index("image") < next(
        i for i, block in enumerate(model.blocks)
        if block.kind == "paragraph" and block.text.startswith("图1-1")
    )


@pytest.mark.uno
def test_extract_formula_like_paragraph_tab_stops(tmp_path):
    """公式样式段落应抽取可用于编号位置判断的制表位。"""
    path = tmp_path / "with_formula_like.docx"
    docx_file = Document()
    para = docx_file.add_paragraph("a = b + c\t(1-1)")
    para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.tab_stops.add_tab_stop(
        Cm(8),
        alignment=WD_TAB_ALIGNMENT.CENTER,
    )
    para.paragraph_format.tab_stops.add_tab_stop(
        Cm(16),
        alignment=WD_TAB_ALIGNMENT.RIGHT,
    )
    docx_file.save(path)

    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))

    para_model = next(
        block for block in model.blocks
        if block.kind == "paragraph" and "(1-1)" in block.text
    )
    assert para_model.tab_stops
    assert {tab.alignment for tab in para_model.tab_stops} & {"center", "right"}


@pytest.mark.uno
def test_extract_marks_ooxml_ole_formula_paragraphs_from_rule_sample():
    """WPS/Word 公式 OLE 对象应通过只读 OOXML 证据映射到段落。"""
    path = "docs/rules/main-text/samples/main-text-formula-format.docx"

    with UnoSession() as session:
        with session.open(path) as doc:
            model = extract(doc, source_path=path)

    formula_paragraphs = [
        block for block in model.blocks
        if block.kind == "paragraph" and block.contains_math
    ]
    assert formula_paragraphs
    assert any("(3-2)" in paragraph.text for paragraph in formula_paragraphs)
