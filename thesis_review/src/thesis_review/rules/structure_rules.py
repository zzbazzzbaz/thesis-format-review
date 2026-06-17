"""结构规则：标题层级、必备章节。"""
from __future__ import annotations

from collections.abc import Iterable

from thesis_review.models import (
    DocumentBlock,
    DocumentModel,
    Issue,
    Location,
    ParagraphBlock,
)


def _paragraphs(document: DocumentModel) -> Iterable[ParagraphBlock]:
    for block in document.blocks:
        if block.kind == "paragraph":
            yield block


def _block_location(block: DocumentBlock) -> Location:
    return Location(
        target="block",
        block_id=block.id,
        block_kind=block.kind,
        flow_index=block.flow_index,
    )


def _document_start_location(document: DocumentModel) -> Location:
    first_para = next(_paragraphs(document), None)
    if first_para is not None:
        return _block_location(first_para)
    if document.blocks:
        return _block_location(document.blocks[0])
    return Location(
        target="block",
        block_id="b-0000",
        block_kind="paragraph",
        flow_index=0,
    )


class HeadingHierarchyRule:
    rule_id = "structure.heading.hierarchy"
    category = "structure"
    severity = "warning"

    def check(self, document: DocumentModel) -> list[Issue]:
        """开发阶段规则：检查标题层级是否跳级（如 1 级直接跳到 3 级，缺少 2 级）。"""
        issues: list[Issue] = []
        prev_level: int | None = None
        for para in _paragraphs(document):
            level = para.outline_level
            if level is None:
                continue
            if prev_level is not None and level > prev_level + 1:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message="标题层级不应跳级",
                        expected=f"{prev_level + 1} 级",
                        actual=f"{level} 级",
                        location=_block_location(para),
                    )
                )
            prev_level = level
        return issues


class RequiredSectionRule:
    rule_id = "structure.section.required"
    category = "structure"
    severity = "error"
    REQUIRED = ("摘要", "关键词", "参考文献")

    @staticmethod
    def _norm(text: str) -> str:
        return text.replace(" ", "").replace("　", "").replace("：", "").replace(":", "")

    def check(self, document: DocumentModel) -> list[Issue]:
        """开发阶段规则：检查是否包含必备章节（摘要、关键词、参考文献），按标题文本归一化后匹配。"""
        heading_texts = [
            self._norm(para.text)
            for para in _paragraphs(document)
            if para.outline_level is not None
        ]
        issues: list[Issue] = []
        for name in self.REQUIRED:
            if not any(name in heading for heading in heading_texts):
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message=f"缺少必备章节：{name}",
                        expected=name,
                        actual=None,
                        location=_document_start_location(document),
                    )
                )
        return issues
