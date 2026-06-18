"""审核结果模型。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from thesis_review.core.models import Issue


class IssueSummary(TypedDict):
    total: int
    error: int
    warning: int
    info: int


@dataclass(frozen=True)
class ReviewResult:
    input_docx: Path
    out_dir: Path
    marked_docx: Path
    issues_json: Path
    issues: list[Issue]

    @property
    def summary(self) -> IssueSummary:
        return summarize_issues(self.issues)


def summarize_issues(issues: list[Issue]) -> IssueSummary:
    summary: IssueSummary = {
        "total": len(issues),
        "error": 0,
        "warning": 0,
        "info": 0,
    }
    for issue in issues:
        summary[issue.severity] += 1
    return summary
