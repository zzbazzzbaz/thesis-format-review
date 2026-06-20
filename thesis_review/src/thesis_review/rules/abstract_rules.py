"""摘要模块规则检查器。"""
from __future__ import annotations

import re
from collections.abc import Iterable
from math import isclose

from thesis_review.core.models import (
    DocumentModel,
    Issue,
    Location,
    ParagraphBlock,
    RunSpan,
)
from thesis_review.core.sections import paragraphs_in_range
from thesis_review.rules.context import RuleContext

_TRAILING_PUNCTUATION_RE = re.compile(r"[，,。.;；：:、]$")
_ASCII_WORD_RE = re.compile(r"[A-Za-z0-9]")
_CHINESE_TEXT_RE = re.compile(r"[\u4e00-\u9fff，。；：、（）《》“”‘’]")


def _paragraphs(document: DocumentModel) -> Iterable[ParagraphBlock]:
    for block in document.blocks:
        if block.kind == "paragraph":
            yield block


def _block_location(para: ParagraphBlock) -> Location:
    return Location(
        target="block",
        block_id=para.id,
        block_kind="paragraph",
        flow_index=para.flow_index,
    )


def _run_location(para: ParagraphBlock, run: RunSpan) -> Location:
    return Location(
        target="run",
        block_id=para.id,
        block_kind="paragraph",
        flow_index=para.flow_index,
        run_id=run.id,
        run_index=run.run_index,
    )


def _non_empty(paragraphs: Iterable[ParagraphBlock]) -> list[ParagraphBlock]:
    return [para for para in paragraphs if para.text.strip()]


def _display_size(size_pt: float | None) -> str | None:
    if size_pt is None:
        return None
    return f"{size_pt:g}pt"


def _display_line_spacing(line_spacing: float | None) -> str | None:
    if line_spacing is None:
        return "未识别"
    return f"{line_spacing:g} 倍"


def _display_indent(indent: float | None) -> str | None:
    if indent is None:
        return "未识别"
    return f"{indent:g} 字符"


def _display_alignment(alignment: str | None) -> str:
    names = {
        "center": "居中",
        "left": "左对齐",
        "right": "右对齐",
        "justify": "两端对齐",
    }
    return names.get(alignment or "", alignment or "未识别")


def _has_size(run: RunSpan, size: float) -> bool:
    return run.size_pt is not None and isclose(run.size_pt, size, abs_tol=0.01)


def _has_line_spacing(para: ParagraphBlock, line_spacing: float) -> bool:
    return (
        para.line_spacing is not None
        and isclose(para.line_spacing, line_spacing, abs_tol=0.01)
    )


def _has_indent(para: ParagraphBlock, indent: float) -> bool:
    return (
        para.first_line_indent_chars is not None
        and isclose(para.first_line_indent_chars, indent, abs_tol=0.05)
    )


def _meaningful_runs(para: ParagraphBlock) -> Iterable[RunSpan]:
    return (run for run in para.runs if run.text.strip())


def _first_bad_run(
    para: ParagraphBlock,
    predicate,
) -> RunSpan | None:
    for run in _meaningful_runs(para):
        if not predicate(run):
            return run
    return None


def _section_paragraphs(context: RuleContext, name: str) -> list[ParagraphBlock]:
    section = context.sections.get(name)
    if section is None:
        return []
    return list(paragraphs_in_range(context.document, section))


def _empty_count_after(paragraphs: list[ParagraphBlock], para: ParagraphBlock) -> int:
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


def _empty_count_before(paragraphs: list[ParagraphBlock], para: ParagraphBlock) -> int:
    try:
        index = paragraphs.index(para)
    except ValueError:
        return 0
    count = 0
    for candidate in reversed(paragraphs[:index]):
        if candidate.text.strip():
            break
        count += 1
    return count


def _find_chinese_keywords(paragraphs: list[ParagraphBlock]) -> ParagraphBlock | None:
    return next(
        (para for para in paragraphs if para.text.lstrip().startswith("关键词")),
        None,
    )


def _find_english_keywords(paragraphs: list[ParagraphBlock]) -> ParagraphBlock | None:
    return next(
        (para for para in paragraphs if para.text.lstrip().lower().startswith("keywords")),
        None,
    )


def _paragraphs_between(
    paragraphs: list[ParagraphBlock],
    start: ParagraphBlock,
    end: ParagraphBlock | None,
) -> list[ParagraphBlock]:
    start_index = paragraphs.index(start)
    end_index = paragraphs.index(end) if end in paragraphs else len(paragraphs)
    return _non_empty(paragraphs[start_index + 1:end_index])


def _append_once(
    issues: list[Issue],
    context: RuleContext,
    rule_id: str,
    actual: str | None,
    location: Location,
) -> None:
    if any(issue.rule_id == rule_id for issue in issues):
        return
    issues.append(
        context.issue_factory.create(rule_id=rule_id, actual=actual, location=location)
    )


def _prefix_runs(para: ParagraphBlock, prefix_length: int) -> list[RunSpan]:
    runs: list[RunSpan] = []
    consumed = 0
    for run in para.runs:
        if consumed >= prefix_length:
            break
        next_consumed = consumed + len(run.text)
        if next_consumed > 0:
            runs.append(run)
        consumed = next_consumed
    return runs


def _first_content_run_after_prefix(
    para: ParagraphBlock,
    prefix_length: int,
) -> RunSpan | None:
    consumed = 0
    for run in para.runs:
        next_consumed = consumed + len(run.text)
        if next_consumed > prefix_length and run.text.strip():
            return run
        consumed = next_consumed
    return None


def _content_runs_after_prefix(
    para: ParagraphBlock,
    prefix_length: int,
) -> Iterable[RunSpan]:
    consumed = 0
    for run in para.runs:
        next_consumed = consumed + len(run.text)
        if next_consumed > prefix_length and run.text.strip():
            yield run
        consumed = next_consumed


def _has_only_chinese_semicolon_separators(content: str) -> bool:
    if ";" in content or "," in content or "；；" in content:
        return False
    return "；" in content


def _run_contains_keyword_content(run: RunSpan) -> bool:
    return bool(_ASCII_WORD_RE.search(run.text))


def _run_contains_chinese_text(run: RunSpan) -> bool:
    return bool(_CHINESE_TEXT_RE.search(run.text))


def _run_contains_ascii_text(run: RunSpan) -> bool:
    return bool(_ASCII_WORD_RE.search(run.text))


class AbstractChineseTitleBodyChecker:
    checker_id = "abstract-chinese-title-body"
    rule_ids = (
        "abstract-chinese-title-001",
        "abstract-chinese-title-002",
        "abstract-chinese-title-003",
        "abstract-chinese-title-004",
        "abstract-chinese-title-005",
        "abstract-chinese-body-001",
        "abstract-chinese-body-002",
        "abstract-chinese-body-003",
        "abstract-chinese-body-004",
        "abstract-chinese-body-005",
        "abstract-chinese-body-006",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        paragraphs = _section_paragraphs(context, "abstract-chinese")
        non_empty = _non_empty(paragraphs)
        if not non_empty:
            return []

        issues: list[Issue] = []
        title = non_empty[0]
        if title.text != "摘    要":
            _append_once(
                issues,
                context,
                "abstract-chinese-title-001",
                title.text,
                _block_location(title),
            )
        bad_title_size = _first_bad_run(title, lambda run: _has_size(run, 16.0))
        if bad_title_size is not None:
            _append_once(
                issues,
                context,
                "abstract-chinese-title-002",
                _display_size(bad_title_size.size_pt),
                _run_location(title, bad_title_size),
            )
        bad_title_font = _first_bad_run(
            title,
            lambda run: run.font_east_asian == "黑体",
        )
        if bad_title_font is not None:
            _append_once(
                issues,
                context,
                "abstract-chinese-title-003",
                bad_title_font.font_east_asian or "未识别",
                _run_location(title, bad_title_font),
            )
        if title.alignment != "center":
            _append_once(
                issues,
                context,
                "abstract-chinese-title-004",
                _display_alignment(title.alignment),
                _block_location(title),
            )
        title_blank_count = _empty_count_after(paragraphs, title)
        if title_blank_count != 1:
            _append_once(
                issues,
                context,
                "abstract-chinese-title-005",
                f"{title_blank_count} 个空段落",
                _block_location(title),
            )

        keywords = _find_chinese_keywords(paragraphs)
        body_paragraphs = _paragraphs_between(paragraphs, title, keywords)
        if body_paragraphs:
            body_anchor = body_paragraphs[0]
            body_blank_count = (
                _empty_count_before(paragraphs, keywords)
                if keywords is not None
                else 0
            )
            if keywords is not None and body_blank_count != 1:
                _append_once(
                    issues,
                    context,
                    "abstract-chinese-body-006",
                    f"{body_blank_count} 个空段落",
                    _block_location(body_anchor),
                )
            for para in body_paragraphs:
                if not _has_line_spacing(para, 1.5):
                    _append_once(
                        issues,
                        context,
                        "abstract-chinese-body-004",
                        _display_line_spacing(para.line_spacing),
                        _block_location(para),
                    )
                if not _has_indent(para, 2.0):
                    _append_once(
                        issues,
                        context,
                        "abstract-chinese-body-005",
                        _display_indent(para.first_line_indent_chars),
                        _block_location(para),
                    )
                bad_body_size = _first_bad_run(
                    para,
                    lambda run: _has_size(run, 12.0),
                )
                if bad_body_size is not None:
                    _append_once(
                        issues,
                        context,
                        "abstract-chinese-body-001",
                        _display_size(bad_body_size.size_pt),
                        _run_location(para, bad_body_size),
                    )
                bad_body_font = _first_bad_run(
                    para,
                    lambda run: (
                        not _run_contains_chinese_text(run)
                        or run.font_east_asian == "宋体"
                    ),
                )
                if bad_body_font is not None:
                    _append_once(
                        issues,
                        context,
                        "abstract-chinese-body-002",
                        bad_body_font.font_east_asian or "未识别",
                        _run_location(para, bad_body_font),
                    )
                bad_body_latin_font = _first_bad_run(
                    para,
                    lambda run: (
                        not _run_contains_ascii_text(run)
                        or run.font_latin == "Times New Roman"
                    ),
                )
                if bad_body_latin_font is not None:
                    _append_once(
                        issues,
                        context,
                        "abstract-chinese-body-003",
                        bad_body_latin_font.font_latin or "未识别",
                        _run_location(para, bad_body_latin_font),
                    )
        return issues


class AbstractChineseKeywordsChecker:
    checker_id = "abstract-chinese-keywords"
    rule_ids = (
        "abstract-chinese-keywords-001",
        "abstract-chinese-keywords-002",
        "abstract-chinese-keywords-003",
        "abstract-chinese-keywords-004",
        "abstract-chinese-keywords-005",
        "abstract-chinese-keywords-006",
        "abstract-chinese-keywords-007",
        "abstract-chinese-keywords-008",
        "abstract-chinese-keywords-009",
        "abstract-chinese-keywords-010",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        paragraphs = _section_paragraphs(context, "abstract-chinese")
        keyword_para = _find_chinese_keywords(paragraphs)
        if keyword_para is None:
            return []

        issues: list[Issue] = []
        text = keyword_para.text.strip()
        if not text.startswith("关键词："):
            _append_once(
                issues,
                context,
                "abstract-chinese-keywords-001",
                text[:4] if text else "未找到",
                _block_location(keyword_para),
            )

        prefix_runs = _prefix_runs(keyword_para, min(len(keyword_para.text), 4))
        if (
            not keyword_para.text.startswith("关键词：")
            or not prefix_runs
            or any(not run.bold for run in prefix_runs)
        ):
            location_run = prefix_runs[0] if prefix_runs else None
            _append_once(
                issues,
                context,
                "abstract-chinese-keywords-002",
                "未加粗",
                _run_location(keyword_para, location_run)
                if location_run is not None
                else _block_location(keyword_para),
            )

        content = text.removeprefix("关键词：")
        if not _has_only_chinese_semicolon_separators(content):
            _append_once(
                issues,
                context,
                "abstract-chinese-keywords-003",
                content,
                _block_location(keyword_para),
            )
        if _TRAILING_PUNCTUATION_RE.search(content):
            _append_once(
                issues,
                context,
                "abstract-chinese-keywords-004",
                content[-1],
                _block_location(keyword_para),
            )
        if not _has_line_spacing(keyword_para, 1.5):
            _append_once(
                issues,
                context,
                "abstract-chinese-keywords-008",
                _display_line_spacing(keyword_para.line_spacing),
                _block_location(keyword_para),
            )
        if not _has_indent(keyword_para, 2.0):
            _append_once(
                issues,
                context,
                "abstract-chinese-keywords-009",
                _display_indent(keyword_para.first_line_indent_chars),
                _block_location(keyword_para),
            )
        if keyword_para.alignment != "justify":
            _append_once(
                issues,
                context,
                "abstract-chinese-keywords-010",
                _display_alignment(keyword_para.alignment),
                _block_location(keyword_para),
            )

        for run in _meaningful_runs(keyword_para):
            if not _has_size(run, 12.0):
                _append_once(
                    issues,
                    context,
                    "abstract-chinese-keywords-005",
                    _display_size(run.size_pt),
                    _run_location(keyword_para, run),
                )
            if _run_contains_chinese_text(run) and run.font_east_asian != "宋体":
                _append_once(
                    issues,
                    context,
                    "abstract-chinese-keywords-006",
                    run.font_east_asian or "未识别",
                    _run_location(keyword_para, run),
                )
            if _run_contains_ascii_text(run) and run.font_latin != "Times New Roman":
                _append_once(
                    issues,
                    context,
                    "abstract-chinese-keywords-007",
                    run.font_latin or "未识别",
                    _run_location(keyword_para, run),
                )
        return issues


class AbstractEnglishTitleBodyChecker:
    checker_id = "abstract-english-title-body"
    rule_ids = (
        "abstract-english-title-001",
        "abstract-english-title-002",
        "abstract-english-title-003",
        "abstract-english-title-004",
        "abstract-english-title-005",
        "abstract-english-title-006",
        "abstract-english-body-001",
        "abstract-english-body-002",
        "abstract-english-body-003",
        "abstract-english-body-004",
        "abstract-english-body-005",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        paragraphs = _section_paragraphs(context, "abstract-english")
        non_empty = _non_empty(paragraphs)
        if not non_empty:
            return []

        issues: list[Issue] = []
        title = non_empty[0]
        if title.text != "ABSTRACT":
            _append_once(
                issues,
                context,
                "abstract-english-title-001",
                title.text,
                _block_location(title),
            )
        bad_title_size = _first_bad_run(title, lambda run: _has_size(run, 16.0))
        if bad_title_size is not None:
            _append_once(
                issues,
                context,
                "abstract-english-title-002",
                _display_size(bad_title_size.size_pt),
                _run_location(title, bad_title_size),
            )
        bad_title_font = _first_bad_run(
            title,
            lambda run: run.font_latin == "Times New Roman",
        )
        if bad_title_font is not None:
            _append_once(
                issues,
                context,
                "abstract-english-title-003",
                bad_title_font.font_latin or "未识别",
                _run_location(title, bad_title_font),
            )
        bad_title_bold = _first_bad_run(title, lambda run: run.bold)
        if bad_title_bold is not None:
            _append_once(
                issues,
                context,
                "abstract-english-title-004",
                "未加粗",
                _run_location(title, bad_title_bold),
            )
        if title.alignment != "center":
            _append_once(
                issues,
                context,
                "abstract-english-title-005",
                _display_alignment(title.alignment),
                _block_location(title),
            )
        title_blank_count = _empty_count_after(paragraphs, title)
        if title_blank_count != 1:
            _append_once(
                issues,
                context,
                "abstract-english-title-006",
                f"{title_blank_count} 个空段落",
                _block_location(title),
            )

        keywords = _find_english_keywords(paragraphs)
        body_paragraphs = _paragraphs_between(paragraphs, title, keywords)
        if body_paragraphs:
            body_anchor = body_paragraphs[0]
            body_blank_count = (
                _empty_count_before(paragraphs, keywords)
                if keywords is not None
                else 0
            )
            if keywords is not None and body_blank_count != 1:
                _append_once(
                    issues,
                    context,
                    "abstract-english-body-005",
                    f"{body_blank_count} 个空段落",
                    _block_location(body_anchor),
                )
            for para in body_paragraphs:
                if not _has_line_spacing(para, 1.5):
                    _append_once(
                        issues,
                        context,
                        "abstract-english-body-003",
                        _display_line_spacing(para.line_spacing),
                        _block_location(para),
                    )
                if not _has_indent(para, 2.0):
                    _append_once(
                        issues,
                        context,
                        "abstract-english-body-004",
                        _display_indent(para.first_line_indent_chars),
                        _block_location(para),
                    )
                bad_body_font = _first_bad_run(
                    para,
                    lambda run: run.font_latin == "Times New Roman",
                )
                if bad_body_font is not None:
                    _append_once(
                        issues,
                        context,
                        "abstract-english-body-001",
                        bad_body_font.font_latin or "未识别",
                        _run_location(para, bad_body_font),
                    )
                bad_body_size = _first_bad_run(
                    para,
                    lambda run: _has_size(run, 12.0),
                )
                if bad_body_size is not None:
                    _append_once(
                        issues,
                        context,
                        "abstract-english-body-002",
                        _display_size(bad_body_size.size_pt),
                        _run_location(para, bad_body_size),
                    )
        return issues


class AbstractEnglishKeywordsChecker:
    checker_id = "abstract-english-keywords"
    rule_ids = (
        "abstract-english-keywords-001",
        "abstract-english-keywords-002",
        "abstract-english-keywords-003",
        "abstract-english-keywords-004",
        "abstract-english-keywords-005",
        "abstract-english-keywords-006",
        "abstract-english-keywords-007",
        "abstract-english-keywords-008",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        paragraphs = _section_paragraphs(context, "abstract-english")
        keyword_para = _find_english_keywords(paragraphs)
        if keyword_para is None:
            return []

        issues: list[Issue] = []
        text = keyword_para.text.strip()
        if not text.startswith("Keywords："):
            _append_once(
                issues,
                context,
                "abstract-english-keywords-001",
                text[:9] if text else "未找到",
                _block_location(keyword_para),
            )

        prefix_length = min(len(keyword_para.text), len("Keywords："))
        prefix_runs = _prefix_runs(keyword_para, prefix_length)
        if (
            not keyword_para.text.startswith("Keywords：")
            or not prefix_runs
            or any(not run.bold for run in prefix_runs)
        ):
            location_run = prefix_runs[0] if prefix_runs else None
            _append_once(
                issues,
                context,
                "abstract-english-keywords-002",
                "未加粗",
                _run_location(keyword_para, location_run)
                if location_run is not None
                else _block_location(keyword_para),
            )

        content = text.removeprefix("Keywords：")
        if not _has_only_chinese_semicolon_separators(content):
            _append_once(
                issues,
                context,
                "abstract-english-keywords-003",
                content,
                _block_location(keyword_para),
            )
        if _TRAILING_PUNCTUATION_RE.search(content):
            _append_once(
                issues,
                context,
                "abstract-english-keywords-004",
                content[-1],
                _block_location(keyword_para),
            )
        if not _has_line_spacing(keyword_para, 1.5):
            _append_once(
                issues,
                context,
                "abstract-english-keywords-007",
                _display_line_spacing(keyword_para.line_spacing),
                _block_location(keyword_para),
            )
        if not _has_indent(keyword_para, 2.0):
            _append_once(
                issues,
                context,
                "abstract-english-keywords-008",
                _display_indent(keyword_para.first_line_indent_chars),
                _block_location(keyword_para),
            )

        for run in _meaningful_runs(keyword_para):
            if not _has_size(run, 12.0):
                _append_once(
                    issues,
                    context,
                    "abstract-english-keywords-005",
                    _display_size(run.size_pt),
                    _run_location(keyword_para, run),
                )
        for run in _content_runs_after_prefix(keyword_para, len("Keywords：")):
            if not _run_contains_keyword_content(run):
                continue
            if run.font_latin != "Times New Roman":
                _append_once(
                    issues,
                    context,
                    "abstract-english-keywords-006",
                    run.font_latin or "未识别",
                    _run_location(keyword_para, run),
                )
        return issues
