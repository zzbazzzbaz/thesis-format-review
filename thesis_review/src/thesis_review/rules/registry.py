"""规则注册表：按配置决定启用哪些规则。"""
from __future__ import annotations

from thesis_review.rules.base import Rule
# 以下 6 条是框架开发阶段规则，暂不启用；保留代码用于测试和参考。
# from thesis_review.rules.format_rules import (
#     BodyFontRule,
#     BodyFontSizeRule,
#     FirstLineIndentRule,
#     LineSpacingRule,
# )
# from thesis_review.rules.structure_rules import (
#     HeadingHierarchyRule,
#     RequiredSectionRule,
# )
from thesis_review.rules.toc_rules import (
    TocEntryFormatRule,
    TocEntrySpacingRule,
    TocTitleRule,
)

RULE_CLASSES: tuple[type[Rule], ...] = (
    # BodyFontRule,
    # BodyFontSizeRule,
    # LineSpacingRule,
    # FirstLineIndentRule,
    # HeadingHierarchyRule,
    # RequiredSectionRule,
    TocTitleRule,
    TocEntrySpacingRule,
    TocEntryFormatRule,
)


def get_rules() -> list[Rule]:
    return [rule_class() for rule_class in RULE_CLASSES]
