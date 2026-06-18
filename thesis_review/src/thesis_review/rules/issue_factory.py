"""统一 Issue 创建。"""
from __future__ import annotations

from thesis_review.core.models import Issue, Location
from thesis_review.rules.catalog import RuleCatalog


class UnknownRuleIdError(KeyError):
    """规则代码引用了不存在的 rule id。"""


class IssueFactory:
    def __init__(self, catalog: RuleCatalog):
        self.catalog = catalog

    def create(
        self,
        rule_id: str,
        actual: str | None,
        location: Location,
    ) -> Issue:
        try:
            rule = self.catalog.get(rule_id)
        except KeyError as exc:
            raise UnknownRuleIdError(rule_id) from exc
        return Issue(
            rule_id=rule.id,
            category="format",
            severity=rule.severity,
            message=rule.message,
            expected=rule.expected,
            actual=actual,
            location=location,
        )
