"""附录模块规则检查器。"""
from __future__ import annotations

from thesis_review.core.models import Issue, ParagraphBlock, RunSpan
from thesis_review.rules.context import RuleContext
from thesis_review.rules.formatting import (
    append_first_bad_run,
    append_issue,
    block_location,
    contains_ascii,
    contains_chinese,
    display_alignment,
    display_indent,
    display_line_spacing,
    display_size,
    empty_count_after,
    has_indent,
    has_line_spacing,
    non_empty,
    section_paragraphs,
)


def _title_and_body(
    context: RuleContext,
) -> tuple[list[ParagraphBlock], ParagraphBlock | None, list[ParagraphBlock]]:
    paragraphs = section_paragraphs(context, "appendix")
    visible = non_empty(paragraphs)
    if not visible:
        return paragraphs, None, []
    title = visible[0]
    start = paragraphs.index(title) + 1 + empty_count_after(paragraphs, title)
    body = [para for para in paragraphs[start:] if para.text.strip()]
    return paragraphs, title, body


def _is_chinese_font(expected: str):
    def predicate(run: RunSpan) -> bool:
        return not contains_chinese(run.text) or run.font_east_asian == expected

    return predicate


def _is_latin_font(expected: str):
    def predicate(run: RunSpan) -> bool:
        return not contains_ascii(run.text) or run.font_latin == expected

    return predicate


class AppendixTitleChecker:
    checker_id = "appendix-title"
    rule_ids = (
        "appendix-title-001",
        "appendix-title-002",
        "appendix-title-003",
        "appendix-title-004",
        "appendix-title-005",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        paragraphs, title, _ = _title_and_body(context)
        if title is None:
            return []
        issues: list[Issue] = []
        if title.text != "附    录":
            append_issue(
                issues,
                context,
                "appendix-title-001",
                title.text,
                block_location(title),
            )
        append_first_bad_run(
            issues,
            context,
            title,
            "appendix-title-002",
            _is_chinese_font("黑体"),
            lambda run: run.font_east_asian or "未识别",
        )
        append_first_bad_run(
            issues,
            context,
            title,
            "appendix-title-003",
            lambda run: run.size_pt == 16.0,
            lambda run: display_size(run.size_pt),
        )
        if title.alignment != "center":
            append_issue(
                issues,
                context,
                "appendix-title-004",
                display_alignment(title.alignment),
                block_location(title),
            )
        blank_count = empty_count_after(paragraphs, title)
        if blank_count != 1:
            append_issue(
                issues,
                context,
                "appendix-title-005",
                f"{blank_count} 个空段落",
                block_location(title),
            )
        return issues


class AppendixBodyChecker:
    checker_id = "appendix-body"
    rule_ids = (
        "appendix-body-001",
        "appendix-body-002",
        "appendix-body-003",
        "appendix-body-004",
        "appendix-body-005",
        "appendix-body-006",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        _, _, body = _title_and_body(context)
        issues: list[Issue] = []
        for para in body:
            append_first_bad_run(
                issues,
                context,
                para,
                "appendix-body-001",
                lambda run: run.size_pt == 12.0,
                lambda run: display_size(run.size_pt),
            )
            append_first_bad_run(
                issues,
                context,
                para,
                "appendix-body-002",
                _is_chinese_font("宋体"),
                lambda run: run.font_east_asian or "未识别",
            )
            append_first_bad_run(
                issues,
                context,
                para,
                "appendix-body-003",
                _is_latin_font("Times New Roman"),
                lambda run: run.font_latin or "未识别",
            )
            if not has_line_spacing(para, 1.5):
                append_issue(
                    issues,
                    context,
                    "appendix-body-004",
                    display_line_spacing(para.line_spacing),
                    block_location(para),
                )
            if not has_indent(para, 2.0):
                append_issue(
                    issues,
                    context,
                    "appendix-body-005",
                    display_indent(para.first_line_indent_chars),
                    block_location(para),
                )
            if para.alignment != "justify":
                append_issue(
                    issues,
                    context,
                    "appendix-body-006",
                    display_alignment(para.alignment),
                    block_location(para),
                )
        return issues
