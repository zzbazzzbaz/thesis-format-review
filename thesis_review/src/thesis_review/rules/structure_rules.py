"""结构规则：标题层级、必备章节。"""
from __future__ import annotations

from thesis_review.models import DocumentModel, Issue, Location


class HeadingHierarchyRule:
    rule_id = "structure.heading.hierarchy"
    category = "structure"
    severity = "warning"

    def check(self, document: DocumentModel) -> list[Issue]:
        """检查标题层级是否跳级（如 1 级直接跳到 3 级，缺少 2 级）。"""
        issues: list[Issue] = []
        prev_level: int | None = None
        for para in document.paragraphs:
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
                        location=Location(
                            kind="paragraph",
                            block_id=para.id,
                            paragraph_index=para.paragraph_index,
                        ),
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
        """检查是否包含必备章节（摘要、关键词、参考文献），按标题文本归一化后匹配。"""
        heading_texts = [
            self._norm(para.text)
            for para in document.paragraphs
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
                        location=Location(
                            kind="paragraph",
                            block_id=document.paragraphs[0].id
                            if document.paragraphs
                            else "p-0000",
                            paragraph_index=0,
                        ),
                    )
                )
        return issues
