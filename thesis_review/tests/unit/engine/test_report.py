"""engine report JSON 输出测试。"""
from __future__ import annotations

import json

from thesis_review.core.models import Issue, Location
from thesis_review.engine.report import result_payload, write_issues_json
from thesis_review.engine.result import ReviewResult, summarize_issues


def make_issue(rule_id: str, severity: str = "error") -> Issue:
    return Issue(
        rule_id=rule_id,
        category="format",
        severity=severity,
        message=f"{rule_id} message",
        expected="expected value",
        actual="actual value",
        location=Location(
            target="block",
            block_id="b-0001",
            block_kind="paragraph",
            flow_index=1,
        ),
    )


def test_summarize_issues_counts_severity():
    issues = [
        make_issue("rule-error", "error"),
        make_issue("rule-warning", "warning"),
        make_issue("rule-info", "info"),
    ]

    assert summarize_issues(issues) == {
        "total": 3,
        "error": 1,
        "warning": 1,
        "info": 1,
    }


def test_result_payload_contains_stable_issue_schema(tmp_path):
    result = ReviewResult(
        input_docx=tmp_path / "input.docx",
        out_dir=tmp_path / "out",
        marked_docx=tmp_path / "out" / "marked.docx",
        issues_json=tmp_path / "out" / "issues.json",
        issues=[make_issue("table-of-contents-title-001")],
    )

    payload = result_payload(result)

    assert payload["input"] == str(tmp_path / "input.docx")
    assert payload["marked_docx"] == str(tmp_path / "out" / "marked.docx")
    assert payload["summary"] == {
        "total": 1,
        "error": 1,
        "warning": 0,
        "info": 0,
    }
    assert payload["issues"][0]["rule_id"] == "table-of-contents-title-001"
    assert payload["issues"][0]["location"]["block_id"] == "b-0001"


def test_write_issues_json_creates_parent_and_utf8_json(tmp_path):
    result = ReviewResult(
        input_docx=tmp_path / "输入.docx",
        out_dir=tmp_path / "nested" / "out",
        marked_docx=tmp_path / "nested" / "out" / "marked.docx",
        issues_json=tmp_path / "nested" / "out" / "issues.json",
        issues=[make_issue("table-of-contents-title-001")],
    )

    write_issues_json(result)

    data = json.loads(result.issues_json.read_text(encoding="utf-8"))
    assert data["issues"][0]["message"] == "table-of-contents-title-001 message"
    assert data["input"].endswith("输入.docx")
