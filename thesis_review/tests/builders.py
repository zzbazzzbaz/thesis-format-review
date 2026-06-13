"""测试用 DocumentModel 构造助手。"""
from thesis_review.models import DocumentModel, ParagraphBlock, RunSpan


def make_run(
    text="正文",
    run_index=0,
    font_east_asian="宋体",
    font_latin=None,
    size_pt=12.0,
    bold=False,
    italic=False,
    block_id="p-0001",
):
    return RunSpan(
        id=f"{block_id}-r-{run_index:04d}",
        text=text,
        run_index=run_index,
        font_east_asian=font_east_asian,
        font_latin=font_latin,
        size_pt=size_pt,
        bold=bold,
        italic=italic,
    )


def make_para(
    paragraph_index=0,
    text="正文",
    style_name="正文",
    outline_level=None,
    alignment="left",
    line_spacing=1.5,
    first_line_indent_chars=2.0,
    runs=None,
):
    block_id = f"p-{paragraph_index:04d}"
    if runs is None:
        runs = [make_run(text=text, block_id=block_id)]
    return ParagraphBlock(
        id=block_id,
        text=text,
        paragraph_index=paragraph_index,
        style_name=style_name,
        outline_level=outline_level,
        alignment=alignment,
        line_spacing=line_spacing,
        first_line_indent_chars=first_line_indent_chars,
        runs=runs,
    )


def make_doc(paragraphs):
    return DocumentModel(source_docx="test.docx", paragraphs=paragraphs)
