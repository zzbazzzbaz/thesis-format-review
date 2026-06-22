"""封面模块规则检查器。"""
from __future__ import annotations

from thesis_review.core.models import Issue, ParagraphBlock, RunSpan
from thesis_review.core.sections import norm_text
from thesis_review.rules.context import RuleContext
from thesis_review.rules.formatting import (
    append_first_bad_run,
    contains_chinese,
    display_size,
    run_location,
    runs_overlapping,
    section_paragraphs,
)


def _cover_paragraphs(context: RuleContext) -> list[ParagraphBlock]:
    return [para for para in section_paragraphs(context, "cover") if para.text.strip()]


def _first_with_norm_prefix(
    paragraphs: list[ParagraphBlock],
    prefixes: tuple[str, ...],
) -> ParagraphBlock | None:
    for para in paragraphs:
        text = norm_text(para.text)
        if any(text.startswith(prefix) for prefix in prefixes):
            return para
    return None


def _all_with_norm_prefix(
    paragraphs: list[ParagraphBlock],
    prefixes: tuple[str, ...],
) -> list[ParagraphBlock]:
    return [
        para for para in paragraphs
        if any(norm_text(para.text).startswith(prefix) for prefix in prefixes)
    ]


def _date_line(paragraphs: list[ParagraphBlock]) -> ParagraphBlock | None:
    for para in paragraphs:
        text = para.text
        if "年" in text and "月" in text and "日" in text:
            return para
    return None


def _requires_chinese_font(expected: str):
    def predicate(run: RunSpan) -> bool:
        return not contains_chinese(run.text) or run.font_east_asian == expected

    return predicate


def _first_bad_run(
    runs: list[RunSpan],
    predicate,
) -> RunSpan | None:
    for run in runs:
        if not predicate(run):
            return run
    return None


def _append_title_issue(
    issues: list[Issue],
    context: RuleContext,
    title: ParagraphBlock,
    runs: list[RunSpan],
    rule_id: str,
    predicate,
    actual,
) -> None:
    run = _first_bad_run(runs, predicate)
    if run is None:
        return
    issues.append(
        context.issue_factory.create(
            rule_id=rule_id,
            actual=actual(run),
            location=run_location(title, run),
        )
    )


class CoverTitleChecker:
    checker_id = "cover-title"
    rule_ids = (
        "cover-title-label-001",
        "cover-title-label-002",
        "cover-title-001",
        "cover-title-002",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        title = _first_with_norm_prefix(_cover_paragraphs(context), ("题目",))
        if title is None:
            return []
        issues: list[Issue] = []
        label_end = title.text.find("：") + 1
        if label_end <= 0:
            label_end = title.text.find(":") + 1
        if label_end <= 0:
            label_end = len("题    目：")

        label_runs = runs_overlapping(title, 0, min(label_end, len(title.text)))
        content_runs = runs_overlapping(
            title,
            min(label_end, len(title.text)),
            len(title.text),
        )
        _append_title_issue(
            issues,
            context,
            title,
            label_runs,
            "cover-title-label-001",
            _requires_chinese_font("仿宋"),
            lambda run: run.font_east_asian or "未识别",
        )
        _append_title_issue(
            issues,
            context,
            title,
            label_runs,
            "cover-title-label-002",
            lambda run: not run.text.strip() or run.size_pt == 16.0,
            lambda run: display_size(run.size_pt),
        )
        _append_title_issue(
            issues,
            context,
            title,
            content_runs,
            "cover-title-001",
            _requires_chinese_font("黑体"),
            lambda run: run.font_east_asian or "未识别",
        )
        _append_title_issue(
            issues,
            context,
            title,
            content_runs,
            "cover-title-002",
            lambda run: not run.text.strip() or run.size_pt == 18.0,
            lambda run: display_size(run.size_pt),
        )
        return issues


class CoverInfoChecker:
    checker_id = "cover-info"
    rule_ids = ("cover-info-001", "cover-info-002", "cover-info-003")
    _prefixes = ("学生姓名", "学号", "院系", "专业年级", "指导教师")

    def check(self, context: RuleContext) -> list[Issue]:
        issues: list[Issue] = []
        for para in _all_with_norm_prefix(_cover_paragraphs(context), self._prefixes):
            append_first_bad_run(
                issues,
                context,
                para,
                "cover-info-001",
                _requires_chinese_font("仿宋"),
                lambda run: run.font_east_asian or "未识别",
            )
            append_first_bad_run(
                issues,
                context,
                para,
                "cover-info-002",
                lambda run: not run.text.strip() or run.size_pt == 16.0,
                lambda run: display_size(run.size_pt),
            )
            append_first_bad_run(
                issues,
                context,
                para,
                "cover-info-003",
                lambda run: not run.text.strip() or run.bold,
                lambda run: "未加粗",
            )
        return issues


class CoverDateChecker:
    checker_id = "cover-date"
    rule_ids = ("cover-date-001", "cover-date-002", "cover-date-003")

    def check(self, context: RuleContext) -> list[Issue]:
        date = _date_line(_cover_paragraphs(context))
        if date is None:
            return []
        issues: list[Issue] = []
        append_first_bad_run(
            issues,
            context,
            date,
            "cover-date-001",
            _requires_chinese_font("仿宋"),
            lambda run: run.font_east_asian or "未识别",
        )
        append_first_bad_run(
            issues,
            context,
            date,
            "cover-date-002",
            lambda run: not run.text.strip() or run.size_pt == 16.0,
            lambda run: display_size(run.size_pt),
        )
        append_first_bad_run(
            issues,
            context,
            date,
            "cover-date-003",
            lambda run: not run.text.strip() or run.bold,
            lambda run: "未加粗",
        )
        return issues
