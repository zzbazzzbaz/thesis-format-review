"""参考文献模块规则检查器。"""
from __future__ import annotations

import re

from thesis_review.core.models import Issue, ParagraphBlock, RunSpan
from thesis_review.rules.context import RuleContext
from thesis_review.rules.formatting import (
    append_first_bad_run,
    append_issue,
    block_location,
    contains_ascii,
    contains_chinese,
    display_line_spacing,
    display_size,
    empty_count_after,
    has_line_spacing,
    non_empty,
    section_paragraphs,
)

_BRACKET_PREFIX_RE = re.compile(r"^(\[[^\]]+\])([ ]*)")
_VALID_NUMBER_RE = re.compile(r"^\[\d+\]")


def _title_and_entries(
    context: RuleContext,
) -> tuple[list[ParagraphBlock], ParagraphBlock | None, list[ParagraphBlock]]:
    paragraphs = section_paragraphs(context, "references")
    visible = non_empty(paragraphs)
    if not visible:
        return paragraphs, None, []
    title = visible[0]
    start = paragraphs.index(title) + 1 + empty_count_after(paragraphs, title)
    entries = [para for para in paragraphs[start:] if para.text.strip()]
    return paragraphs, title, entries


def _is_chinese_font(run: RunSpan) -> bool:
    return not contains_chinese(run.text) or run.font_east_asian == "宋体"


def _is_latin_font(run: RunSpan) -> bool:
    return not contains_ascii(run.text) or run.font_latin == "Times New Roman"


class ReferencesTitleChecker:
    checker_id = "references-title"
    rule_ids = ("references-title-001", "references-title-002")

    def check(self, context: RuleContext) -> list[Issue]:
        paragraphs, title, _ = _title_and_entries(context)
        if title is None:
            return []
        issues: list[Issue] = []
        if title.text != "参考文献":
            append_issue(
                issues,
                context,
                "references-title-001",
                title.text,
                block_location(title),
            )
        blank_count = empty_count_after(paragraphs, title)
        if blank_count != 1:
            append_issue(
                issues,
                context,
                "references-title-002",
                f"{blank_count} 个空段落",
                block_location(title),
            )
        return issues


class ReferencesEntryChecker:
    checker_id = "references-entry"
    rule_ids = (
        "references-entry-001",
        "references-entry-002",
        "references-entry-003",
        "references-entry-004",
        "references-entry-005",
        "references-entry-006",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        _, _, entries = _title_and_entries(context)
        issues: list[Issue] = []
        for para in entries:
            self._check_numbering(context, para, issues)
            self._check_format(context, para, issues)
        return issues

    def _check_numbering(
        self,
        context: RuleContext,
        para: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        text = para.text
        if _VALID_NUMBER_RE.match(text) is None:
            actual = text.split(" ", 1)[0] if text.strip() else "未识别"
            append_issue(
                issues,
                context,
                "references-entry-001",
                actual,
                block_location(para),
            )
        match = _BRACKET_PREFIX_RE.match(text)
        if match is None:
            append_issue(
                issues,
                context,
                "references-entry-002",
                "未找到编号后空格",
                block_location(para),
            )
            return
        spaces = match.group(2)
        if len(spaces) != 1:
            append_issue(
                issues,
                context,
                "references-entry-002",
                f"{len(spaces)} 个空格",
                block_location(para),
            )

    def _check_format(
        self,
        context: RuleContext,
        para: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        append_first_bad_run(
            issues,
            context,
            para,
            "references-entry-003",
            _is_chinese_font,
            lambda run: run.font_east_asian or "未识别",
        )
        append_first_bad_run(
            issues,
            context,
            para,
            "references-entry-004",
            _is_latin_font,
            lambda run: run.font_latin or "未识别",
        )
        append_first_bad_run(
            issues,
            context,
            para,
            "references-entry-005",
            lambda run: run.size_pt == 12.0,
            lambda run: display_size(run.size_pt),
        )
        if not has_line_spacing(para, 1.5):
            append_issue(
                issues,
                context,
                "references-entry-006",
                display_line_spacing(para.line_spacing),
                block_location(para),
            )
