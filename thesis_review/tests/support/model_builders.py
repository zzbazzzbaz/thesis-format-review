"""测试用 DocumentModel 构造助手。"""
from thesis_review.core.models import (
    DocumentModel,
    FormattedTextRun,
    HeaderFooterParagraph,
    ImageBlock,
    PageStyleInfo,
    ParagraphBlock,
    RunSpan,
    TableBlock,
    TabStopInfo,
)


def make_run(
    text="正文",
    run_index=0,
    font_east_asian="宋体",
    font_latin=None,
    size_pt=12.0,
    bold=False,
    italic=False,
    superscript=False,
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
        superscript=superscript,
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
    is_empty=None,
    page_break_before=False,
    page_style_name=None,
    contains_math=False,
    math_object_count=0,
    tab_stops=None,
):
    if type_index is None:
        type_index = flow_index
    block_id = f"b-{flow_index:04d}"
    if is_empty is None:
        is_empty = not text.strip()
    if runs is None:
        runs = [] if is_empty else [make_run(text=text, block_id=block_id)]
    else:
        runs = [
            run.model_copy(update={"id": f"{block_id}-r-{idx:04d}", "run_index": idx})
            for idx, run in enumerate(runs)
        ]
    return ParagraphBlock(
        id=block_id,
        flow_index=flow_index,
        type_index=type_index,
        page_style_name=page_style_name,
        text=text,
        style_name=style_name,
        outline_level=outline_level,
        alignment=alignment,
        line_spacing=line_spacing,
        first_line_indent_chars=first_line_indent_chars,
        page_break_before=page_break_before,
        is_empty=is_empty,
        runs=runs,
        contains_math=contains_math,
        math_object_count=math_object_count,
        tab_stops=tab_stops or [],
    )


def make_table(
    flow_index=0,
    type_index=0,
    text="表格内容",
    row_count=2,
    column_count=2,
    page_style_name=None,
):
    return TableBlock(
        id=f"b-{flow_index:04d}",
        flow_index=flow_index,
        type_index=type_index,
        page_style_name=page_style_name,
        text=text,
        row_count=row_count,
        column_count=column_count,
    )


def make_image(
    flow_index=0,
    type_index=0,
    name="Picture 1",
    alt_text="示意图",
    width_mm=None,
    height_mm=None,
    page_style_name=None,
):
    return ImageBlock(
        id=f"b-{flow_index:04d}",
        flow_index=flow_index,
        type_index=type_index,
        page_style_name=page_style_name,
        name=name,
        alt_text=alt_text,
        width_mm=width_mm,
        height_mm=height_mm,
    )


def make_doc(blocks, page_styles=None):
    return DocumentModel(
        source_docx="test.docx",
        blocks=blocks,
        page_styles=page_styles or [],
    )


def make_formatted_run(
    text="正文",
    run_index=0,
    font_east_asian="宋体",
    font_latin="Times New Roman",
    size_pt=12.0,
    bold=False,
    italic=False,
):
    return FormattedTextRun(
        text=text,
        run_index=run_index,
        font_east_asian=font_east_asian,
        font_latin=font_latin,
        size_pt=size_pt,
        bold=bold,
        italic=italic,
    )


def make_header_footer_para(
    text="山东石油化工学院本科毕业设计（论文）",
    paragraph_index=0,
    alignment="center",
    runs=None,
    has_page_number_field=False,
    page_number_text=None,
    page_number_format=None,
):
    return HeaderFooterParagraph(
        text=text,
        paragraph_index=paragraph_index,
        alignment=alignment,
        runs=runs or [make_formatted_run(text=text)],
        has_page_number_field=has_page_number_field,
        page_number_text=page_number_text,
        page_number_format=page_number_format,
    )


def make_page_style(
    name="正文",
    header_paragraphs=None,
    footer_paragraphs=None,
):
    header_paragraphs = header_paragraphs or []
    footer_paragraphs = footer_paragraphs or []
    return PageStyleInfo(
        name=name,
        header_text="\n".join(p.text for p in header_paragraphs) or None,
        footer_text="\n".join(p.text for p in footer_paragraphs) or None,
        header_paragraphs=header_paragraphs,
        footer_paragraphs=footer_paragraphs,
    )


def make_tab_stop(position_mm=80.0, alignment="center"):
    return TabStopInfo(position_mm=position_mm, alignment=alignment)
