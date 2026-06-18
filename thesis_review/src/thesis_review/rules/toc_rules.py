"""目录模块规则检查器。"""
from __future__ import annotations

import re
from collections.abc import Iterable
from math import isclose

from thesis_review.models import (
    DocumentModel,
    Issue,
    Location,
    ParagraphBlock,
    RunSpan,
)
from thesis_review.rules.context import RuleContext
from thesis_review.sections import is_toc_title, paragraphs_in_range

_FIRST_LEVEL_RE = re.compile(r"^(第[一二三四五六七八九十\d]+章)( *)(.+)\t\d+\s*$")
_LOWER_LEVEL_RE = re.compile(r"^(\d+(?:\.\d+){1,2})( *)(.+)\t\d+\s*$")


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


def _document_start_location(document: DocumentModel) -> Location:
    first = next(_paragraphs(document), None)
    if first is not None:
        return _block_location(first)
    return Location(
        target="block",
        block_id="b-0000",
        block_kind="paragraph",
        flow_index=0,
    )


def _toc_title(document: DocumentModel) -> ParagraphBlock | None:
    return next(
        (para for para in _paragraphs(document) if is_toc_title(para)),
        None,
    )


def _empty_count_after(document: DocumentModel, title: ParagraphBlock) -> int:
    blocks = document.blocks
    pos = next(i for i, block in enumerate(blocks) if block.id == title.id)
    count = 0
    for block in blocks[pos + 1:]:
        if block.kind != "paragraph":
            break
        if block.text.strip():
            break
        count += 1
    return count


def _display_alignment(alignment: str | None) -> str | None:
    if alignment == "center":
        return "居中"
    if alignment == "left":
        return "左对齐"
    return alignment or "未识别"


def _display_line_spacing(line_spacing: float | None) -> str | None:
    if line_spacing is None:
        return None
    return f"{line_spacing:g} 倍"


def _display_size(size_pt: float | None) -> str | None:
    if size_pt is None:
        return None
    return f"{size_pt:g}pt"


def _entry_paragraphs(context: RuleContext) -> list[ParagraphBlock]:
    section = context.sections.get("table-of-contents")
    if section is None:
        return []
    return [
        para
        for para in paragraphs_in_range(context.document, section)
        if para.text.strip() and not is_toc_title(para)
    ]


class TableOfContentsTitleChecker:
    checker_id = "table-of-contents-title"
    rule_ids = (
        "table-of-contents-title-001",
        "table-of-contents-title-002",
        "table-of-contents-title-003",
        "table-of-contents-title-004",
        "table-of-contents-title-005",
        "table-of-contents-title-006",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        title = _toc_title(context.document)
        if title is None:
            return [
                context.issue_factory.create(
                    rule_id="table-of-contents-title-001",
                    actual="未找到目录",
                    location=_document_start_location(context.document),
                )
            ]

        issues: list[Issue] = []
        if title.text != "目    录":
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-title-001",
                    actual=title.text,
                    location=_block_location(title),
                )
            )
        if title.alignment != "center":
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-title-004",
                    actual=_display_alignment(title.alignment),
                    location=_block_location(title),
                )
            )
        if title.line_spacing is not None and not isclose(
            title.line_spacing,
            1.5,
            abs_tol=0.01,
        ):
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-title-005",
                    actual=_display_line_spacing(title.line_spacing),
                    location=_block_location(title),
                )
            )
        for run in title.runs:
            if not run.text.strip():
                continue
            if run.font_east_asian and run.font_east_asian != "黑体":
                issues.append(
                    context.issue_factory.create(
                        rule_id="table-of-contents-title-003",
                        actual=run.font_east_asian,
                        location=_block_location(title),
                    )
                )
            if run.size_pt is not None and not isclose(
                run.size_pt,
                16.0,
                abs_tol=0.01,
            ):
                issues.append(
                    context.issue_factory.create(
                        rule_id="table-of-contents-title-002",
                        actual=_display_size(run.size_pt),
                        location=_block_location(title),
                    )
                )
        blank_count = _empty_count_after(context.document, title)
        if blank_count != 1:
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-title-006",
                    actual=f"{blank_count} 个空段落",
                    location=_block_location(title),
                )
            )
        return issues


class TableOfContentsEntryChecker:
    checker_id = "table-of-contents-entry"
    rule_ids = (
        "table-of-contents-entry-001",
        "table-of-contents-entry-002",
        "table-of-contents-entry-003",
        "table-of-contents-entry-004",
        "table-of-contents-entry-005",
        "table-of-contents-entry-006",
        "table-of-contents-entry-007",
        "table-of-contents-entry-008",
    )

    def check(self, context: RuleContext) -> list[Issue]:
        if "table-of-contents" not in context.sections:
            return []
        issues: list[Issue] = []
        for para in _entry_paragraphs(context):
            self._check_spacing(context, para, issues)
            self._check_paragraph_format(context, para, issues)
            for run in para.runs:
                self._check_run(context, para, run, issues)
        return issues

    def _check_spacing(
        self,
        context: RuleContext,
        para: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        match = _FIRST_LEVEL_RE.match(para.text)
        if match is not None:
            spaces = match.group(2)
            if len(spaces) != 2:
                issues.append(
                    context.issue_factory.create(
                        rule_id="table-of-contents-entry-001",
                        actual=f"{len(spaces)} 个空格",
                        location=_block_location(para),
                    )
                )
            return

        match = _LOWER_LEVEL_RE.match(para.text)
        if match is None:
            return
        spaces = match.group(2)
        level = match.group(1).count(".") + 1
        rule_id = (
            "table-of-contents-entry-002"
            if level == 2
            else "table-of-contents-entry-003"
        )
        if len(spaces) != 1:
            issues.append(
                context.issue_factory.create(
                    rule_id=rule_id,
                    actual=f"{len(spaces)} 个空格",
                    location=_block_location(para),
                )
            )

    def _check_paragraph_format(
        self,
        context: RuleContext,
        para: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        if para.line_spacing is not None and not isclose(
            para.line_spacing,
            1.5,
            abs_tol=0.01,
        ):
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-entry-007",
                    actual=_display_line_spacing(para.line_spacing),
                    location=_block_location(para),
                )
            )

    def _check_run(
        self,
        context: RuleContext,
        para: ParagraphBlock,
        run: RunSpan,
        issues: list[Issue],
    ) -> None:
        if not run.text.strip() or run.text == "\t":
            return
        location = _run_location(para, run)
        if run.font_east_asian and run.font_east_asian != "宋体":
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-entry-004",
                    actual=run.font_east_asian,
                    location=location,
                )
            )
        if run.font_latin and run.font_latin != "Times New Roman":
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-entry-005",
                    actual=run.font_latin,
                    location=location,
                )
            )
        if run.size_pt is not None and not isclose(
            run.size_pt,
            12.0,
            abs_tol=0.01,
        ):
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-entry-006",
                    actual=_display_size(run.size_pt),
                    location=location,
                )
            )
        if run.bold:
            issues.append(
                context.issue_factory.create(
                    rule_id="table-of-contents-entry-008",
                    actual="加粗",
                    location=location,
                )
            )
