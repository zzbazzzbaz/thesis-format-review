"""UNO 读文档属性 → DocumentModel。

枚举段落与 text portion，读取 UNO 已渲染的有效格式（字体/字号/行距/
大纲/缩进等），产出引擎无关的 DocumentModel。
"""
from __future__ import annotations

import re

from thesis_review.core.models import (
    DocumentBlock,
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
from thesis_review.adapters.ooxml.structure import (
    PageNumberFormatInfo,
    footer_page_number_format,
    match_paragraph_object_flags,
    paragraph_object_infos,
)
from thesis_review.adapters.uno.traversal import TraversedBlock
from thesis_review.adapters.uno.traversal import blocks as iter_blocks
from thesis_review.adapters.uno.traversal import text_portions

# ── 常量 ────────────────────────────────────────────────────────────

_MM100_PER_PT = 35.2778       # 1pt = 0.352778mm = 35.2778 (1/100 mm)
_ADJUST = {0: "left", 1: "right", 2: "justify", 3: "center"}
_TAB_ADJUST = {
    "LEFT": "left",
    "CENTER": "center",
    "RIGHT": "right",
    "DECIMAL": "decimal",
}
_LINE_MODE_PROP = 0            # com.sun.star.style.LineSpacingMode.PROP

# ── 辅助 ────────────────────────────────────────────────────────────


def _safe_float(val) -> float | None:
    """安全转换为 float；None/空/异常 → None。"""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _mm100_to_mm(value) -> float | None:
    val = _safe_float(value)
    if val is None:
        return None
    return round(val / 100.0, 2)


def _is_bold(weight_val) -> bool:
    """CharWeight >= 150.0 (BOLD) 为粗体。"""
    w = _safe_float(weight_val)
    return w is not None and w >= 150.0


def _is_italic(posture_val) -> bool:
    """CharPosture == 2 (ITALIC) 或 FontSlant.ITALIC 为斜体。

    UNO 返回 enum 实例；pyuno 支持与整数比较。
    """
    try:
        return int(posture_val) == 2
    except (TypeError, ValueError):
        return False


def _is_superscript(escapement_val) -> bool:
    """UNO CharEscapement > 0 表示上标。"""
    try:
        return int(escapement_val) > 0
    except (TypeError, ValueError):
        return False


def _outline_level(para) -> int | None:
    """UNO OutlineLevel：1=Heading1 → 模型 0；0=正文 → None。"""
    lvl = int(getattr(para, "OutlineLevel", 0) or 0)
    return (lvl - 1) if lvl >= 1 else None


def _alignment(para) -> str | None:
    """UNO ParaAdjust → 字符串。"""
    val = int(getattr(para, "ParaAdjust", 0) or 0)
    return _ADJUST.get(val)


def _line_spacing(para) -> float | None:
    """UNO ParaLineSpacing 结构体 → 行距倍数。"""
    ls = getattr(para, "ParaLineSpacing", None)
    if ls is None:
        return None
    try:
        mode = int(ls.Mode)
        height = int(ls.Height)
    except (TypeError, ValueError, AttributeError):
        return None
    if mode == _LINE_MODE_PROP and height > 0:
        return height / 100.0
    return None


def _first_line_indent_chars(para, first_run_pt: float | None) -> float:
    """UNO ParaFirstLineIndent (1/100mm) → 字符数。"""
    indent = int(getattr(para, "ParaFirstLineIndent", 0) or 0)
    if indent == 0:
        return 0.0
    pt = first_run_pt or 12.0
    char_mm100 = pt * _MM100_PER_PT
    if char_mm100 <= 0:
        return 0.0
    return round(indent / char_mm100, 2)


def _page_break_before(para) -> bool:
    """读取显式段前分页符；无法识别时按无分页处理。"""
    break_type = getattr(para, "BreakType", None)
    if break_type is None:
        return False
    return "PAGE_BEFORE" in str(break_type)


def _page_style_name(para) -> str | None:
    return getattr(para, "PageDescName", None) or getattr(para, "PageStyleName", None)


def _tab_stops(para) -> list[TabStopInfo]:
    stops: list[TabStopInfo] = []
    for stop in getattr(para, "ParaTabStops", ()) or ():
        alignment = _TAB_ADJUST.get(str(getattr(stop, "Alignment", "")).split("'")[-2], "unknown")
        stops.append(
            TabStopInfo(
                position_mm=_mm100_to_mm(getattr(stop, "Position", None)),
                alignment=alignment,
            )
        )
    return stops


def _math_object_count(para) -> int:
    count = 0
    try:
        enum = para.createEnumeration()
    except AttributeError:
        return 0
    while enum.hasMoreElements():
        portion = enum.nextElement()
        if getattr(portion, "TextPortionType", "") in {"Frame", "TextContent"}:
            count += 1
    return count


def _safe_count(obj, accessor: str) -> int | None:
    try:
        return int(getattr(obj, accessor)().getCount())
    except (AttributeError, TypeError, ValueError):
        return None


def _table_text(table) -> str:
    texts: list[str] = []
    try:
        names = table.getCellNames()
    except AttributeError:
        return ""
    for name in names:
        try:
            text = table.getCellByName(name).getString()
        except AttributeError:
            continue
        if text:
            texts.append(text)
    return "\n".join(texts)


def _extract_paragraph(
    block: TraversedBlock,
    *,
    has_ooxml_object: bool = False,
) -> ParagraphBlock:
    elem = block.element
    text = elem.getString()

    runs: list[RunSpan] = []
    block_id = f"b-{block.flow_index:04d}"
    for r_idx, portion in enumerate(text_portions(elem)):
        portion_text = portion.getString()

        # 字体属性：Asian 变体优先（中文文本），fallback 到通用变体
        ch_height = _safe_float(getattr(portion, "CharHeightAsian", None))
        if ch_height is None:
            ch_height = _safe_float(getattr(portion, "CharHeight", None))

        ch_weight = getattr(portion, "CharWeightAsian", None)
        if ch_weight is None:
            ch_weight = getattr(portion, "CharWeight", None)

        ch_posture = getattr(portion, "CharPostureAsian", None)
        if ch_posture is None:
            ch_posture = getattr(portion, "CharPosture", None)

        runs.append(RunSpan(
            id=f"{block_id}-r-{r_idx:04d}",
            text=portion_text,
            run_index=r_idx,
            font_east_asian=getattr(portion, "CharFontNameAsian", None),
            font_latin=getattr(portion, "CharFontName", None),
            size_pt=ch_height,
            bold=_is_bold(ch_weight),
            italic=_is_italic(ch_posture),
            superscript=_is_superscript(getattr(portion, "CharEscapement", None)),
        ))

    first_run_pt = runs[0].size_pt if runs else None
    math_count = _math_object_count(elem)
    if has_ooxml_object and math_count == 0:
        math_count = 1
    return ParagraphBlock(
        id=block_id,
        flow_index=block.flow_index,
        type_index=block.type_index,
        page_style_name=_page_style_name(elem),
        text=text,
        style_name=getattr(elem, "ParaStyleName", None),
        outline_level=_outline_level(elem),
        alignment=_alignment(elem),
        line_spacing=_line_spacing(elem),
        first_line_indent_chars=_first_line_indent_chars(elem, first_run_pt),
        page_break_before=_page_break_before(elem),
        is_empty=not text.strip(),
        runs=runs,
        contains_math=math_count > 0,
        math_object_count=math_count,
        tab_stops=_tab_stops(elem),
    )


def _extract_table(block: TraversedBlock) -> TableBlock:
    table = block.element
    return TableBlock(
        id=f"b-{block.flow_index:04d}",
        flow_index=block.flow_index,
        type_index=block.type_index,
        page_style_name=None,
        row_count=_safe_count(table, "getRows"),
        column_count=_safe_count(table, "getColumns"),
        text=_table_text(table),
    )


def _extract_image(block: TraversedBlock) -> ImageBlock:
    shape = block.element
    size = getattr(shape, "Size", None)
    return ImageBlock(
        id=f"b-{block.flow_index:04d}",
        flow_index=block.flow_index,
        type_index=block.type_index,
        name=getattr(shape, "Name", None),
        alt_text=getattr(shape, "Description", None) or getattr(shape, "Title", None),
        width_mm=_mm100_to_mm(getattr(size, "Width", None)),
        height_mm=_mm100_to_mm(getattr(size, "Height", None)),
    )


def _formatted_runs(text_obj) -> list[FormattedTextRun]:
    runs: list[FormattedTextRun] = []
    try:
        enum = text_obj.createEnumeration()
    except AttributeError:
        return runs
    run_index = 0
    while enum.hasMoreElements():
        portion = enum.nextElement()
        try:
            text = portion.getString()
        except AttributeError:
            continue
        if not text:
            continue
        size = _safe_float(getattr(portion, "CharHeightAsian", None))
        if size is None:
            size = _safe_float(getattr(portion, "CharHeight", None))
        weight = getattr(portion, "CharWeightAsian", None)
        if weight is None:
            weight = getattr(portion, "CharWeight", None)
        posture = getattr(portion, "CharPostureAsian", None)
        if posture is None:
            posture = getattr(portion, "CharPosture", None)
        runs.append(
            FormattedTextRun(
                text=text,
                run_index=run_index,
                font_east_asian=getattr(portion, "CharFontNameAsian", None),
                font_latin=getattr(portion, "CharFontName", None),
                size_pt=size,
                bold=_is_bold(weight),
                italic=_is_italic(posture),
            )
        )
        run_index += 1
    return runs


def _guess_page_number_format(text: str) -> str | None:
    value = text.strip()
    if not value:
        return None
    if value.isdigit():
        return "arabic"
    if re.fullmatch(r"[IVXLCDM]+", value, re.IGNORECASE):
        return "roman"
    return "unknown"


def _merge_page_number_run_format(
    runs: list[FormattedTextRun],
    page_number: PageNumberFormatInfo | None,
) -> list[FormattedTextRun]:
    if page_number is None:
        return runs
    for index, run in enumerate(runs):
        if not run.text.strip().isdigit():
            continue
        runs[index] = run.model_copy(
            update={
                "font_east_asian": page_number.font_east_asian or run.font_east_asian,
                "font_latin": page_number.font_latin or run.font_latin,
                "size_pt": page_number.size_pt if page_number.size_pt is not None else run.size_pt,
            }
        )
        break
    return runs


def _header_footer_paragraphs(
    text_obj,
    *,
    page_number: PageNumberFormatInfo | None = None,
) -> list[HeaderFooterParagraph]:
    paragraphs: list[HeaderFooterParagraph] = []
    try:
        enum = text_obj.createEnumeration()
    except AttributeError:
        return paragraphs
    index = 0
    while enum.hasMoreElements():
        elem = enum.nextElement()
        try:
            is_paragraph = elem.supportsService("com.sun.star.text.Paragraph")
        except AttributeError:
            is_paragraph = False
        if not is_paragraph:
            continue
        text = elem.getString()
        runs = _formatted_runs(elem)
        page_number_text = text.strip() or None
        if page_number_text and page_number_text.isdigit():
            runs = _merge_page_number_run_format(runs, page_number)
        paragraphs.append(
            HeaderFooterParagraph(
                text=text,
                paragraph_index=index,
                alignment=_alignment(elem),
                runs=runs,
                has_page_number_field=False,
                page_number_text=page_number_text,
                page_number_format=_guess_page_number_format(text),
            )
        )
        index += 1
    return paragraphs


def _extract_page_styles(
    doc,
    *,
    page_number: PageNumberFormatInfo | None = None,
) -> list[PageStyleInfo]:
    styles: list[PageStyleInfo] = []
    try:
        page_styles = doc.getStyleFamilies().getByName("PageStyles")
        names = page_styles.getElementNames()
    except AttributeError:
        return styles
    for name in names:
        style = page_styles.getByName(name)
        header_paragraphs = _header_footer_paragraphs(getattr(style, "HeaderText", None))
        footer_paragraphs = _header_footer_paragraphs(
            getattr(style, "FooterText", None),
            page_number=page_number,
        )
        styles.append(
            PageStyleInfo(
                name=name,
                width_mm=_mm100_to_mm(getattr(style, "Width", None)),
                height_mm=_mm100_to_mm(getattr(style, "Height", None)),
                margin_top_mm=_mm100_to_mm(getattr(style, "TopMargin", None)),
                margin_bottom_mm=_mm100_to_mm(getattr(style, "BottomMargin", None)),
                margin_left_mm=_mm100_to_mm(getattr(style, "LeftMargin", None)),
                margin_right_mm=_mm100_to_mm(getattr(style, "RightMargin", None)),
                header_text="\n".join(
                    para.text for para in header_paragraphs if para.text.strip()
                ) or None,
                footer_text="\n".join(
                    para.text for para in footer_paragraphs if para.text.strip()
                ) or None,
                header_paragraphs=header_paragraphs,
                footer_paragraphs=footer_paragraphs,
            )
        )
    return styles


# ── 主函数 ──────────────────────────────────────────────────────────


def extract(doc, source_path: str = "unknown.docx") -> DocumentModel:
    """从 UNO 文本文档中抽取段落、run 及其格式属性。

    Args:
        doc: UNO com.sun.star.text.XTextDocument
        source_path: 源文件路径，写入 DocumentModel.source_docx

    Returns:
        DocumentModel，段落按 UNO 枚举顺序排列
    """
    blocks: list[DocumentBlock] = []
    traversed_blocks = iter_blocks(doc)
    paragraph_texts = [
        block.element.getString()
        for block in traversed_blocks
        if block.kind == "paragraph"
    ]
    ooxml_object_flags = match_paragraph_object_flags(
        paragraph_texts,
        paragraph_object_infos(source_path),
    )
    ooxml_page_number = footer_page_number_format(source_path)
    paragraph_index = 0
    for block in traversed_blocks:
        if block.kind == "paragraph":
            has_ooxml_object = (
                paragraph_index < len(ooxml_object_flags)
                and ooxml_object_flags[paragraph_index]
            )
            blocks.append(
                _extract_paragraph(
                    block,
                    has_ooxml_object=has_ooxml_object,
                )
            )
            paragraph_index += 1
        elif block.kind == "table":
            blocks.append(_extract_table(block))
        elif block.kind == "image":
            blocks.append(_extract_image(block))

    return DocumentModel(
        source_docx=source_path,
        blocks=blocks,
        page_styles=_extract_page_styles(doc, page_number=ooxml_page_number),
    )
