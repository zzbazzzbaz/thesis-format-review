"""规则检查器共享格式工具。"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from math import isclose

from thesis_review.core.models import Issue, Location, ParagraphBlock, RunSpan
from thesis_review.core.sections import paragraphs_in_range
from thesis_review.rules.context import RuleContext

_ASCII_TEXT_RE = re.compile(r"[A-Za-z0-9]")
_CHINESE_TEXT_RE = re.compile(r"[\u4e00-\u9fff，。；：、（）《》“”‘’]")


def block_location(para: ParagraphBlock) -> Location:
    return Location(
        target="block",
        block_id=para.id,
        block_kind="paragraph",
        flow_index=para.flow_index,
    )


def run_location(para: ParagraphBlock, run: RunSpan) -> Location:
    return Location(
        target="run",
        block_id=para.id,
        block_kind="paragraph",
        flow_index=para.flow_index,
        run_id=run.id,
        run_index=run.run_index,
    )


def section_paragraphs(context: RuleContext, name: str) -> list[ParagraphBlock]:
    section = context.sections.get(name)
    if section is None:
        return []
    return list(paragraphs_in_range(context.document, section))


def non_empty(paragraphs: Iterable[ParagraphBlock]) -> list[ParagraphBlock]:
    return [para for para in paragraphs if para.text.strip()]


def empty_count_after(paragraphs: list[ParagraphBlock], para: ParagraphBlock) -> int:
    try:
        index = paragraphs.index(para)
    except ValueError:
        return 0
    count = 0
    for candidate in paragraphs[index + 1:]:
        if candidate.text.strip():
            break
        count += 1
    return count


def display_size(size_pt: float | None) -> str:
    if size_pt is None:
        return "未识别"
    return f"{size_pt:g}pt"


def display_line_spacing(line_spacing: float | None) -> str:
    if line_spacing is None:
        return "未识别"
    return f"{line_spacing:g} 倍"


def display_indent(indent: float | None) -> str:
    if indent is None:
        return "未识别"
    return f"{indent:g} 字符"


def display_alignment(alignment: str | None) -> str:
    names = {
        "center": "居中",
        "left": "左对齐",
        "right": "右对齐",
        "justify": "两端对齐",
    }
    return names.get(alignment or "", alignment or "未识别")


def has_size(run: RunSpan, size: float) -> bool:
    return run.size_pt is not None and isclose(run.size_pt, size, abs_tol=0.01)


def has_line_spacing(para: ParagraphBlock, line_spacing: float) -> bool:
    return (
        para.line_spacing is not None
        and isclose(para.line_spacing, line_spacing, abs_tol=0.01)
    )


def has_indent(para: ParagraphBlock, indent: float) -> bool:
    return (
        para.first_line_indent_chars is not None
        and isclose(para.first_line_indent_chars, indent, abs_tol=0.05)
    )


def meaningful_runs(para: ParagraphBlock) -> list[RunSpan]:
    return [run for run in para.runs if run.text.strip()]


def first_bad_run(
    para: ParagraphBlock,
    predicate: Callable[[RunSpan], bool],
) -> RunSpan | None:
    for run in meaningful_runs(para):
        if not predicate(run):
            return run
    return None


def contains_chinese(text: str) -> bool:
    return bool(_CHINESE_TEXT_RE.search(text))


def contains_ascii(text: str) -> bool:
    return bool(_ASCII_TEXT_RE.search(text))


def append_issue(
    issues: list[Issue],
    context: RuleContext,
    rule_id: str,
    actual: str | None,
    location: Location,
) -> None:
    issues.append(
        context.issue_factory.create(
            rule_id=rule_id,
            actual=actual,
            location=location,
        )
    )


def append_first_bad_run(
    issues: list[Issue],
    context: RuleContext,
    para: ParagraphBlock,
    rule_id: str,
    predicate: Callable[[RunSpan], bool],
    actual: Callable[[RunSpan], str | None],
) -> None:
    bad = first_bad_run(para, predicate)
    if bad is None:
        return
    append_issue(
        issues,
        context,
        rule_id=rule_id,
        actual=actual(bad),
        location=run_location(para, bad),
    )
