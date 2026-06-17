"""目录 C 类规则。"""
from __future__ import annotations

from collections.abc import Iterable
from math import isclose

from thesis_review.models import (
    DocumentModel,
    Issue,
    Location,
    ParagraphBlock,
    RunSpan,
)
from thesis_review.sections import is_toc_title


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


class TocTitleRule:
    rule_id = "C001"
    category = "format"
    severity = "error"

    def check(self, document: DocumentModel) -> list[Issue]:
        title = _toc_title(document)
        if title is None:
            return [
                Issue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message="缺少目录标题：目    录",
                    expected="目    录",
                    actual=None,
                    location=_document_start_location(document),
                )
            ]

        issues: list[Issue] = []
        self._check_text(title, issues)
        self._check_paragraph_format(title, issues)
        self._check_runs(title, issues)
        self._check_blank_after(document, title, issues)
        return issues

    def _add(
        self,
        para: ParagraphBlock,
        issues: list[Issue],
        message: str,
        expected: str,
        actual: str | None,
    ) -> None:
        issues.append(
            Issue(
                rule_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                message=message,
                expected=expected,
                actual=actual,
                location=_block_location(para),
            )
        )

    def _check_text(
        self,
        title: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        if title.text != "目    录":
            self._add(
                title,
                issues,
                "目录标题应为“目    录”，中间 4 个普通空格",
                "目    录",
                title.text,
            )

    def _check_paragraph_format(
        self,
        title: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        if title.alignment != "center":
            self._add(title, issues, "目录标题应居中", "center", title.alignment)
        if title.line_spacing is not None and not isclose(
            title.line_spacing,
            1.5,
            abs_tol=0.01,
        ):
            self._add(
                title,
                issues,
                "目录标题行距应为 1.5 倍",
                "1.5",
                str(title.line_spacing),
            )

    def _check_runs(
        self,
        title: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        for run in title.runs:
            if not run.text.strip():
                continue
            if run.font_east_asian and run.font_east_asian != "黑体":
                self._add(
                    title,
                    issues,
                    "目录标题中文字体应为黑体",
                    "黑体",
                    run.font_east_asian,
                )
            if run.size_pt is not None and not isclose(
                run.size_pt,
                16.0,
                abs_tol=0.01,
            ):
                self._add(
                    title,
                    issues,
                    "目录标题字号应为三号(16pt)",
                    "16.0",
                    str(run.size_pt),
                )

    def _check_blank_after(
        self,
        document: DocumentModel,
        title: ParagraphBlock,
        issues: list[Issue],
    ) -> None:
        count = _empty_count_after(document, title)
        if count == 0:
            self._add(
                title,
                issues,
                "目录标题后应空一行",
                "1 个空段落",
                "0 个空段落",
            )
        elif count > 1:
            self._add(
                title,
                issues,
                "目录标题后只能空一行",
                "1 个空段落",
                f"{count} 个空段落",
            )
