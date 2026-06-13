"""规则注册表：按配置决定启用哪些规则。"""
from __future__ import annotations

from src.rules.base import Rule
from src.rules.format_rules import (
    BodyFontRule,
    BodyFontSizeRule,
    FirstLineIndentRule,
    LineSpacingRule,
)
from src.rules.structure_rules import (
    HeadingHierarchyRule,
    RequiredSectionRule,
)

ALL_RULES: list[Rule] = [
    BodyFontRule(),
    BodyFontSizeRule(),
    LineSpacingRule(),
    FirstLineIndentRule(),
    HeadingHierarchyRule(),
    RequiredSectionRule(),
]


def get_rules() -> list[Rule]:
    return ALL_RULES
