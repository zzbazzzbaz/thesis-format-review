"""测试用 DocumentModel 构造助手。"""
from thesis_review.models import (
    DocumentModel,
    ImageBlock,
    ParagraphBlock,
    RunSpan,
    TableBlock,
)


def make_run(
    text="正文",
    run_index=0,
    font_east_asian="宋体",
    font_latin=None,
    size_pt=12.0,
    bold=False,
    italic=False,
    block_id="b-0001",
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
    flow_index=0,
    type_index=None,
    text="正文",
    style_name="正文",
    outline_level=None,
    alignment="left",
    line_spacing=1.5,
    first_line_indent_chars=2.0,
    runs=None,
):
    if type_index is None:
        type_index = flow_index
    block_id = f"b-{flow_index:04d}"
    if runs is None:
        runs = [make_run(text=text, block_id=block_id)]
    else:
        runs = [
            run.model_copy(update={"id": f"{block_id}-r-{idx:04d}", "run_index": idx})
            for idx, run in enumerate(runs)
        ]
    return ParagraphBlock(
        id=block_id,
        flow_index=flow_index,
        type_index=type_index,
        text=text,
        style_name=style_name,
        outline_level=outline_level,
        alignment=alignment,
        line_spacing=line_spacing,
        first_line_indent_chars=first_line_indent_chars,
        runs=runs,
    )


def make_table(flow_index=0, type_index=0, text="表格内容", row_count=2, column_count=2):
    return TableBlock(
        id=f"b-{flow_index:04d}",
        flow_index=flow_index,
        type_index=type_index,
        text=text,
        row_count=row_count,
        column_count=column_count,
    )


def make_image(flow_index=0, type_index=0, name="Picture 1", alt_text="示意图"):
    return ImageBlock(
        id=f"b-{flow_index:04d}",
        flow_index=flow_index,
        type_index=type_index,
        name=name,
        alt_text=alt_text,
    )


def make_doc(blocks):
    return DocumentModel(source_docx="test.docx", blocks=blocks)
