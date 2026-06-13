"""Rule 协议：所有规则的统一接口。"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from thesis_review.models import DocumentModel, Issue


@runtime_checkable
class Rule(Protocol):
    rule_id: str
    category: str
    severity: str

    def check(self, document: DocumentModel) -> list[Issue]:
        ...
