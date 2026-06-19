"""规则检查器注册表。"""
from __future__ import annotations

from thesis_review.rules.base import RuleChecker
from thesis_review.rules.abstract_rules import (
    AbstractChineseKeywordsChecker,
    AbstractChineseTitleBodyChecker,
    AbstractEnglishKeywordsChecker,
    AbstractEnglishTitleBodyChecker,
)
from thesis_review.rules.toc_rules import (
    TableOfContentsEntryChecker,
    TableOfContentsTitleChecker,
)

CHECKER_CLASSES: tuple[type[RuleChecker], ...] = (
    AbstractChineseTitleBodyChecker,
    AbstractChineseKeywordsChecker,
    AbstractEnglishTitleBodyChecker,
    AbstractEnglishKeywordsChecker,
    TableOfContentsTitleChecker,
    TableOfContentsEntryChecker,
)


def get_checkers() -> list[RuleChecker]:
    return [checker_class() for checker_class in CHECKER_CLASSES]
