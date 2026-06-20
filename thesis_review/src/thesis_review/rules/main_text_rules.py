"""正文模块规则检查器。"""
from __future__ import annotations

import re

from thesis_review.core.models import Issue, ParagraphBlock, RunSpan
from thesis_review.core.sections import is_toc_entry
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
    run_location,
    section_paragraphs,
)

_CHINESE_NUMERAL_RE = re.compile(r"^[一二三四五六七八九十]+$")
_H1_RE = re.compile(r"^(第(.+?)章)( *)(.+)$")
_H2_RE = re.compile(r"^(\d+\.\d+)( *)(.+)$")
_H3_RE = re.compile(r"^(\d+\.\d+\.\d+)( *)(.+)$")
_MALFORMED_H2_RE = re.compile(r"^(\d{2,})( +)(\S.+)$")
_MALFORMED_H3_RE = re.compile(r"^(\d+\.\d{2,})( *)(.+)$")
_FIGURE_CAPTION_RE = re.compile(r"^图\d+-\d+ ")
_TABLE_CAPTION_RE = re.compile(r"^表\d+-\d+ ")
_FORMULA_LIKE_RE = re.compile(r"^\s*(?:[A-Za-z0-9+\-*/=()]+|\(\d+-\d+\))\s*$")
_PLACEHOLDER_RE = re.compile(r"^[…\.．。]{2,}$")
_CONTINUED_TABLE_RE = re.compile(r"^续表\s*\d+-\d+")
_CITATION_RE = re.compile(r"\[[A-Za-z0-9]+\]")
_VALID_CITATION_RE = re.compile(r"^\[\d+\]$")


def _main_paragraphs(context: RuleContext) -> list[ParagraphBlock]:
    return [para for para in section_paragraphs(context, "main-text") if para.text.strip()]


def _is_chinese_font(expected: str):
    def predicate(run: RunSpan) -> bool:
        return not contains_chinese(run.text) or run.font_east_asian == expected

    return predicate


def _is_latin_font(expected: str):
    def predicate(run: RunSpan) -> bool:
        return not contains_ascii(run.text) or run.font_latin == expected

    return predicate


def _is_h1_candidate(para: ParagraphBlock) -> bool:
    return para.text.startswith("第") and "章" in para.text and not is_toc_entry(para.text)


def _is_h2_candidate(para: ParagraphBlock) -> bool:
    text = para.text.strip()
    return bool(_H2_RE.match(text) or _MALFORMED_H2_RE.match(text))


def _is_h3_candidate(para: ParagraphBlock) -> bool:
    text = para.text.strip()
    return bool(_H3_RE.match(text) or _MALFORMED_H3_RE.match(text))


def _is_caption_or_formula(para: ParagraphBlock) -> bool:
    text = para.text.strip()
    return bool(
        _FIGURE_CAPTION_RE.match(text)
        or _TABLE_CAPTION_RE.match(text)
        or _FORMULA_LIKE_RE.match(text)
        or _PLACEHOLDER_RE.match(text)
        or _CONTINUED_TABLE_RE.match(text)
    )


def _is_heading(para: ParagraphBlock) -> bool:
    return _is_h1_candidate(para) or _is_h2_candidate(para) or _is_h3_candidate(para)


def _run_ranges(para: ParagraphBlock) -> list[tuple[int, int, RunSpan]]:
    ranges: list[tuple[int, int, RunSpan]] = []
    cursor = 0
    for run in para.runs:
        start = cursor
        cursor += len(run.text)
        ranges.append((start, cursor, run))
    return ranges


def _runs_overlapping(para: ParagraphBlock, start: int, end: int) -> list[RunSpan]:
    return [
        run for run_start, run_end, run in _run_ranges(para)
        if run_end > start and run_start < end and run.text.strip()
    ]


class MainTextHeadingChecker:
    checker_id = "main-text-heading"
    rule_ids = (
        "main-text-heading-level-one-001",
        "main-text-heading-level-one-002",
        "main-text-heading-level-one-003",
        "main-text-heading-level-one-004",
        "main-text-heading-level-one-005",
        "main-text-heading-level-one-006",
        "main-text-heading-level-two-001",
        "main-text-heading-level-two-002",
        "main-text-heading-level-two-003",
        "main-text-heading-level-two-004",
        "main-text-heading-level-two-005",
        "main-text-heading-level-two-006",
        "main-text-heading-level-three-001",
        "main-text-heading-level-three-002",
        "main-text-heading-level-three-003",
        "main-text-heading-level-three-004",
        "main-text-heading-level-three-005",
        "main-text-heading-level-three-006",
        "main-text-heading-level-three-007",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        paragraphs = section_paragraphs(context, "main-text")
        issues: list[Issue] = []
        for para in [p for p in paragraphs if p.text.strip()]:
            if _is_h1_candidate(para):
                self._check_h1(context, paragraphs, para, issues)
            elif _is_h3_candidate(para):
                self._check_h3(context, para, issues)
            elif _is_h2_candidate(para):
                self._check_h2(context, para, issues)
        return issues

    def _check_h1(
        self,
        context: RuleContext,
        paragraphs: list[ParagraphBlock],
        para: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        match = _H1_RE.match(para.text.strip())
        numeral = match.group(2) if match else ""
        spaces = match.group(3) if match else ""
        if match is None or _CHINESE_NUMERAL_RE.fullmatch(numeral) is None:
            append_issue(
                issues,
                context,
                "main-text-heading-level-one-001",
                para.text.strip().split(" ", 1)[0],
                block_location(para),
            )
        if len(spaces) != 2:
            append_issue(
                issues,
                context,
                "main-text-heading-level-one-002",
                f"{len(spaces)} 个空格",
                block_location(para),
            )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-one-003",
            _is_chinese_font("黑体"),
            lambda run: run.font_east_asian or "未识别",
        )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-one-004",
            lambda run: run.size_pt == 16.0,
            lambda run: display_size(run.size_pt),
        )
        blank_count = empty_count_after(paragraphs, para)
        if blank_count != 1:
            append_issue(
                issues,
                context,
                "main-text-heading-level-one-005",
                f"{blank_count} 个空段落",
                block_location(para),
            )
        if not para.page_break_before:
            append_issue(
                issues,
                context,
                "main-text-heading-level-one-006",
                "未另起一页",
                block_location(para),
            )

    def _check_h2(
        self,
        context: RuleContext,
        para: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        match = _H2_RE.match(para.text.strip())
        spaces = match.group(2) if match else ""
        if match is None:
            append_issue(
                issues,
                context,
                "main-text-heading-level-two-001",
                para.text.strip().split(" ", 1)[0],
                block_location(para),
            )
        if len(spaces) != 1:
            append_issue(
                issues,
                context,
                "main-text-heading-level-two-002",
                f"{len(spaces)} 个空格",
                block_location(para),
            )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-two-003",
            _is_chinese_font("黑体"),
            lambda run: run.font_east_asian or "未识别",
        )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-two-004",
            lambda run: run.size_pt == 14.0,
            lambda run: display_size(run.size_pt),
        )
        if not has_line_spacing(para, 1.5):
            append_issue(
                issues,
                context,
                "main-text-heading-level-two-005",
                display_line_spacing(para.line_spacing),
                block_location(para),
            )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-two-006",
            _is_latin_font("Times New Roman"),
            lambda run: run.font_latin or "未识别",
        )

    def _check_h3(
        self,
        context: RuleContext,
        para: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        match = _H3_RE.match(para.text.strip())
        spaces = match.group(2) if match else ""
        if match is None:
            append_issue(
                issues,
                context,
                "main-text-heading-level-three-001",
                para.text.strip().split(" ", 1)[0],
                block_location(para),
            )
        if len(spaces) != 1:
            append_issue(
                issues,
                context,
                "main-text-heading-level-three-002",
                f"{len(spaces)} 个空格",
                block_location(para),
            )
        if not has_indent(para, 2.0):
            append_issue(
                issues,
                context,
                "main-text-heading-level-three-003",
                display_indent(para.first_line_indent_chars),
                block_location(para),
            )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-three-004",
            _is_chinese_font("黑体"),
            lambda run: run.font_east_asian or "未识别",
        )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-three-005",
            lambda run: run.size_pt == 12.0,
            lambda run: display_size(run.size_pt),
        )
        if not has_line_spacing(para, 1.5):
            append_issue(
                issues,
                context,
                "main-text-heading-level-three-006",
                display_line_spacing(para.line_spacing),
                block_location(para),
            )
        append_first_bad_run(
            issues,
            context,
            para,
            "main-text-heading-level-three-007",
            _is_latin_font("Times New Roman"),
            lambda run: run.font_latin or "未识别",
        )


class MainTextParagraphChecker:
    checker_id = "main-text-paragraph"
    rule_ids = (
        "main-text-paragraph-001",
        "main-text-paragraph-002",
        "main-text-paragraph-003",
        "main-text-paragraph-004",
        "main-text-paragraph-005",
        "main-text-paragraph-006",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        issues: list[Issue] = []
        for para in _main_paragraphs(context):
            if _is_heading(para) or _is_caption_or_formula(para):
                continue
            append_first_bad_run(
                issues,
                context,
                para,
                "main-text-paragraph-001",
                lambda run: run.size_pt == 12.0,
                lambda run: display_size(run.size_pt),
            )
            append_first_bad_run(
                issues,
                context,
                para,
                "main-text-paragraph-002",
                _is_chinese_font("宋体"),
                lambda run: run.font_east_asian or "未识别",
            )
            append_first_bad_run(
                issues,
                context,
                para,
                "main-text-paragraph-003",
                _is_latin_font("Times New Roman"),
                lambda run: run.font_latin or "未识别",
            )
            if not has_indent(para, 2.0):
                append_issue(
                    issues,
                    context,
                    "main-text-paragraph-004",
                    display_indent(para.first_line_indent_chars),
                    block_location(para),
                )
            if not has_line_spacing(para, 1.5):
                append_issue(
                    issues,
                    context,
                    "main-text-paragraph-005",
                    display_line_spacing(para.line_spacing),
                    block_location(para),
                )
            if para.alignment != "justify":
                append_issue(
                    issues,
                    context,
                    "main-text-paragraph-006",
                    display_alignment(para.alignment),
                    block_location(para),
                )
        return issues


class MainTextReferenceCitationChecker:
    checker_id = "main-text-reference-citation"
    rule_ids = (
        "main-text-reference-citation-001",
        "main-text-reference-citation-002",
        "main-text-reference-citation-003",
        "main-text-reference-citation-004",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        issues: list[Issue] = []
        for para in _main_paragraphs(context):
            if _is_heading(para) or _is_caption_or_formula(para):
                continue
            for match in _CITATION_RE.finditer(para.text):
                token = match.group(0)
                runs = _runs_overlapping(para, match.start(), match.end())
                if _VALID_CITATION_RE.fullmatch(token) is None:
                    append_issue(
                        issues,
                        context,
                        "main-text-reference-citation-001",
                        token,
                        block_location(para),
                    )
                for run in runs:
                    if not run.superscript:
                        append_issue(
                            issues,
                            context,
                            "main-text-reference-citation-002",
                            "非上标",
                            run_location(para, run),
                        )
                        break
                for run in runs:
                    if run.size_pt != 12.0:
                        append_issue(
                            issues,
                            context,
                            "main-text-reference-citation-003",
                            display_size(run.size_pt),
                            run_location(para, run),
                        )
                        break
                for run in runs:
                    if run.font_latin != "Times New Roman":
                        append_issue(
                            issues,
                            context,
                            "main-text-reference-citation-004",
                            run.font_latin or "未识别",
                            run_location(para, run),
                        )
                        break
        return issues
