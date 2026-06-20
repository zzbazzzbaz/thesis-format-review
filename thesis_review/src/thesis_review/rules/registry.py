"""规则检查器注册表。"""
from __future__ import annotations

from thesis_review.rules.base import RuleChecker
from thesis_review.rules.abstract_rules import (
    AbstractChineseKeywordsChecker,
    AbstractChineseTitleBodyChecker,
    AbstractEnglishKeywordsChecker,
    AbstractEnglishTitleBodyChecker,
)
from thesis_review.rules.acknowledgements_rules import (
    AcknowledgementsBodyChecker,
    AcknowledgementsTitleChecker,
)
from thesis_review.rules.appendix_rules import (
    AppendixBodyChecker,
    AppendixTitleChecker,
)
from thesis_review.rules.cover_rules import (
    CoverDateChecker,
    CoverInfoChecker,
    CoverTitleChecker,
)
from thesis_review.rules.main_text_rules import (
    MainTextHeadingChecker,
    MainTextParagraphChecker,
    MainTextReferenceCitationChecker,
)
from thesis_review.rules.references_rules import (
    ReferencesEntryChecker,
    ReferencesTitleChecker,
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
    CoverTitleChecker,
    CoverInfoChecker,
    CoverDateChecker,
    ReferencesTitleChecker,
    ReferencesEntryChecker,
    AcknowledgementsTitleChecker,
    AcknowledgementsBodyChecker,
    AppendixTitleChecker,
    AppendixBodyChecker,
    MainTextHeadingChecker,
    MainTextParagraphChecker,
    MainTextReferenceCitationChecker,
)


def get_checkers() -> list[RuleChecker]:
    return [checker_class() for checker_class in CHECKER_CLASSES]
