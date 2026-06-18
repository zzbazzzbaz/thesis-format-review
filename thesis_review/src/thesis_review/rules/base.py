"""RuleChecker 协议：所有规则检查器的统一接口。"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from thesis_review.models import Issue


@runtime_checkable
class RuleChecker(Protocol):
    checker_id: str
    rule_ids: tuple[str, ...]

    def check(self, context) -> list[Issue]:
        ...


Rule = RuleChecker
