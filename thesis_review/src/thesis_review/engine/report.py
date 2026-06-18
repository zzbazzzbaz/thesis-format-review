"""审核结果 JSON 报告。"""
from __future__ import annotations

import json
from typing import Any

from thesis_review.engine.result import ReviewResult


def result_payload(result: ReviewResult) -> dict[str, Any]:
    return {
        "input": str(result.input_docx),
        "marked_docx": str(result.marked_docx),
        "summary": result.summary,
        "issues": [issue.model_dump(mode="json") for issue in result.issues],
    }


def write_issues_json(result: ReviewResult) -> None:
    result.issues_json.parent.mkdir(parents=True, exist_ok=True)
    result.issues_json.write_text(
        json.dumps(result_payload(result), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
