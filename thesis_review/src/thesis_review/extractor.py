"""UNO 读文档属性 → DocumentModel。

枚举段落与 text portion，读取 UNO 已渲染的有效格式（字体/字号/行距/
大纲/缩进等），产出引擎无关的 DocumentModel。
"""
from __future__ import annotations

from thesis_review.core.models import (
    DocumentBlock,
    DocumentModel,
    ParagraphBlock,
    RunSpan,
    TableBlock,
)
from thesis_review.uno_traversal import TraversedBlock
from thesis_review.uno_traversal import blocks as iter_blocks
from thesis_review.uno_traversal import text_portions

# ── 常量 ────────────────────────────────────────────────────────────

_MM100_PER_PT = 35.2778       # 1pt = 0.352778mm = 35.2778 (1/100 mm)
_ADJUST = {0: "left", 1: "right", 2: "justify", 3: "center"}
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


def _extract_paragraph(block: TraversedBlock) -> ParagraphBlock:
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
        ))

    first_run_pt = runs[0].size_pt if runs else None
    return ParagraphBlock(
        id=block_id,
        flow_index=block.flow_index,
        type_index=block.type_index,
        text=text,
        style_name=getattr(elem, "ParaStyleName", None),
        outline_level=_outline_level(elem),
        alignment=_alignment(elem),
        line_spacing=_line_spacing(elem),
        first_line_indent_chars=_first_line_indent_chars(elem, first_run_pt),
        page_break_before=_page_break_before(elem),
        is_empty=not text.strip(),
        runs=runs,
    )


def _extract_table(block: TraversedBlock) -> TableBlock:
    table = block.element
    return TableBlock(
        id=f"b-{block.flow_index:04d}",
        flow_index=block.flow_index,
        type_index=block.type_index,
        row_count=_safe_count(table, "getRows"),
        column_count=_safe_count(table, "getColumns"),
        text=_table_text(table),
    )


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
    for block in iter_blocks(doc):
        if block.kind == "paragraph":
            blocks.append(_extract_paragraph(block))
        elif block.kind == "table":
            blocks.append(_extract_table(block))

    return DocumentModel(source_docx=source_path, blocks=blocks)
