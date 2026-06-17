"""规则注册表：按配置决定启用哪些规则。"""
from __future__ import annotations

from thesis_review.rules.base import Rule
from thesis_review.rules.toc_rules import (
    TocEntryFormatRule,
    TocEntrySpacingRule,
    TocTitleRule,
)

RULE_CLASSES: tuple[type[Rule], ...] = (
    TocTitleRule,
    TocEntrySpacingRule,
    TocEntryFormatRule,
)


def get_rules() -> list[Rule]:
    return [rule_class() for rule_class in RULE_CLASSES]
