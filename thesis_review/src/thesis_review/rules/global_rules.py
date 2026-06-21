"""整体模块页眉和页脚页码规则检查器。"""
from __future__ import annotations

import re

from thesis_review.core.models import (
    DocumentBlock,
    FormattedTextRun,
    HeaderFooterParagraph,
    Issue,
    PageStyleInfo,
)
from thesis_review.rules.context import RuleContext
from thesis_review.rules.formatting import (
    append_issue,
    block_location,
    contains_chinese,
    display_alignment,
    display_size,
    section_blocks,
)

EXPECTED_HEADER = "山东石油化工学院本科毕业设计（论文）"
HEADER_SECTIONS = (
    "abstract-chinese",
    "abstract-english",
    "table-of-contents",
    "main-text",
    "references",
    "acknowledgements",
    "appendix",
)
FOOTER_SECTIONS = ("main-text", "references", "acknowledgements", "appendix")
_ARABIC_RE = re.compile(r"^\d+$")
_ROMAN_RE = re.compile(r"^[IVXLCDM]+$", re.IGNORECASE)


def _styles_by_name(context: RuleContext) -> dict[str, PageStyleInfo]:
    return {style.name: style for style in context.document.page_styles}


def _first_blocks_by_style(
    context: RuleContext,
    section_names: tuple[str, ...],
) -> dict[str, DocumentBlock]:
    out: dict[str, DocumentBlock] = {}
    for section_name in section_names:
        for block in section_blocks(context, section_name):
            if block.page_style_name and block.page_style_name not in out:
                out[block.page_style_name] = block
    return out


def _visible_runs(paragraph: HeaderFooterParagraph) -> list[FormattedTextRun]:
    return [run for run in paragraph.runs if run.text.strip()]


def _paragraph_text(paragraphs: list[HeaderFooterParagraph]) -> str:
    return "\n".join(para.text for para in paragraphs if para.text.strip()).strip()


def _first_visible_paragraph(
    paragraphs: list[HeaderFooterParagraph],
) -> HeaderFooterParagraph | None:
    return next((para for para in paragraphs if para.text.strip()), None)


def _is_arabic_page_number(paragraph: HeaderFooterParagraph) -> bool:
    if paragraph.page_number_format == "arabic":
        return True
    text = (paragraph.page_number_text or paragraph.text).strip()
    return bool(_ARABIC_RE.fullmatch(text))


def _is_page_number_candidate(paragraph: HeaderFooterParagraph) -> bool:
    if paragraph.has_page_number_field:
        return True
    text = (paragraph.page_number_text or paragraph.text).strip()
    return bool(_ARABIC_RE.fullmatch(text) or _ROMAN_RE.fullmatch(text))


class GlobalHeaderChecker:
    checker_id = "global-header"
    rule_ids = (
        "global-header-001",
        "global-header-002",
        "global-header-003",
        "global-header-004",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        issues: list[Issue] = []
        styles = _styles_by_name(context)
        for style_name, anchor in _first_blocks_by_style(context, HEADER_SECTIONS).items():
            style = styles.get(style_name)
            paragraphs = style.header_paragraphs if style is not None else []
            header_text = _paragraph_text(paragraphs)
            if not header_text:
                append_issue(
                    issues,
                    context,
                    "global-header-001",
                    "未识别",
                    block_location(anchor),
                )
                continue
            if header_text != EXPECTED_HEADER:
                append_issue(
                    issues,
                    context,
                    "global-header-001",
                    header_text,
                    block_location(anchor),
                )
            paragraph = _first_visible_paragraph(paragraphs)
            if paragraph is None:
                continue
            for run in _visible_runs(paragraph):
                if contains_chinese(run.text) and run.font_east_asian != "黑体":
                    append_issue(
                        issues,
                        context,
                        "global-header-002",
                        run.font_east_asian or "未识别",
                        block_location(anchor),
                    )
                    break
            for run in _visible_runs(paragraph):
                if run.size_pt != 10.5:
                    append_issue(
                        issues,
                        context,
                        "global-header-003",
                        display_size(run.size_pt),
                        block_location(anchor),
                    )
                    break
            if paragraph.alignment != "center":
                append_issue(
                    issues,
                    context,
                    "global-header-004",
                    display_alignment(paragraph.alignment),
                    block_location(anchor),
                )
        return issues


class GlobalFooterPageNumberChecker:
    checker_id = "global-footer-page-number"
    rule_ids = (
        "global-footer-page-number-001",
        "global-footer-page-number-003",
        "global-footer-page-number-004",
        "global-footer-page-number-005",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        issues: list[Issue] = []
        styles = _styles_by_name(context)
        for style_name, anchor in _first_blocks_by_style(context, FOOTER_SECTIONS).items():
            style = styles.get(style_name)
            paragraphs = style.footer_paragraphs if style is not None else []
            paragraph = next(
                (candidate for candidate in paragraphs if _is_page_number_candidate(candidate)),
                None,
            )
            if paragraph is None:
                append_issue(
                    issues,
                    context,
                    "global-footer-page-number-001",
                    "未识别页码",
                    block_location(anchor),
                )
                continue
            if not _is_arabic_page_number(paragraph):
                append_issue(
                    issues,
                    context,
                    "global-footer-page-number-001",
                    paragraph.page_number_text or paragraph.text or "未识别页码",
                    block_location(anchor),
                )
            if paragraph.alignment != "center":
                append_issue(
                    issues,
                    context,
                    "global-footer-page-number-003",
                    display_alignment(paragraph.alignment),
                    block_location(anchor),
                )
            runs = _visible_runs(paragraph)
            for run in runs:
                if run.font_latin != "Times New Roman":
                    append_issue(
                        issues,
                        context,
                        "global-footer-page-number-004",
                        run.font_latin or "未识别",
                        block_location(anchor),
                    )
                    break
            for run in runs:
                if run.size_pt != 10.5:
                    append_issue(
                        issues,
                        context,
                        "global-footer-page-number-005",
                        display_size(run.size_pt),
                        block_location(anchor),
                    )
                    break
        return issues
