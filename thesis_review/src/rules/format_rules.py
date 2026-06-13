"""格式规则：字体、字号、行距、缩进。"""
from __future__ import annotations

from thesis_review.models import DocumentModel, Issue, Location


class BodyFontRule:
    rule_id = "format.body.font"
    category = "format"
    severity = "error"
    EXPECTED_FONT = "宋体"

    def check(self, document: DocumentModel) -> list[Issue]:
        issues: list[Issue] = []
        for para in document.paragraphs:
            if para.outline_level is not None:
                continue
            for run in para.runs:
                if run.font_east_asian and run.font_east_asian != self.EXPECTED_FONT:
                    issues.append(
                        Issue(
                            rule_id=self.rule_id,
                            category=self.category,
                            severity=self.severity,
                            message=f"正文中文字体应为{self.EXPECTED_FONT}",
                            expected=self.EXPECTED_FONT,
                            actual=run.font_east_asian,
                            location=Location(
                                kind="run",
                                block_id=para.id,
                                paragraph_index=para.paragraph_index,
                                run_id=run.id,
                                run_index=run.run_index,
                            ),
                        )
                    )
        return issues


class BodyFontSizeRule:
    rule_id = "format.body.size"
    category = "format"
    severity = "error"
    EXPECTED_PT = 12.0

    def check(self, document: DocumentModel) -> list[Issue]:
        issues: list[Issue] = []
        for para in document.paragraphs:
            if para.outline_level is not None:
                continue
            for run in para.runs:
                if run.size_pt is not None and run.size_pt != self.EXPECTED_PT:
                    issues.append(
                        Issue(
                            rule_id=self.rule_id,
                            category=self.category,
                            severity=self.severity,
                            message="正文字号应为小四(12pt)",
                            expected=str(self.EXPECTED_PT),
                            actual=str(run.size_pt),
                            location=Location(
                                kind="run",
                                block_id=para.id,
                                paragraph_index=para.paragraph_index,
                                run_id=run.id,
                                run_index=run.run_index,
                            ),
                        )
                    )
        return issues


class LineSpacingRule:
    rule_id = "format.body.line_spacing"
    category = "format"
    severity = "warning"
    EXPECTED = 1.5

    def check(self, document: DocumentModel) -> list[Issue]:
        issues: list[Issue] = []
        for para in document.paragraphs:
            if para.outline_level is not None:
                continue
            if para.line_spacing is not None and para.line_spacing != self.EXPECTED:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message="正文行距应为 1.5 倍",
                        expected=str(self.EXPECTED),
                        actual=str(para.line_spacing),
                        location=Location(
                            kind="paragraph",
                            block_id=para.id,
                            paragraph_index=para.paragraph_index,
                        ),
                    )
                )
        return issues


class FirstLineIndentRule:
    rule_id = "format.body.indent"
    category = "format"
    severity = "warning"
    EXPECTED_CHARS = 2.0

    def check(self, document: DocumentModel) -> list[Issue]:
        issues: list[Issue] = []
        for para in document.paragraphs:
            if para.outline_level is not None:
                continue
            indent = para.first_line_indent_chars
            if indent is not None and indent != self.EXPECTED_CHARS:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message="正文首行缩进应为 2 字符",
                        expected=str(self.EXPECTED_CHARS),
                        actual=str(indent),
                        location=Location(
                            kind="paragraph",
                            block_id=para.id,
                            paragraph_index=para.paragraph_index,
                        ),
                    )
                )
        return issues
