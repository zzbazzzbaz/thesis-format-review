"""目录 C 类规则真实 Word 样本测试。"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("uno")

from thesis_review.extractor import extract
from thesis_review.rules.toc_rules import (
    TocEntryFormatRule,
    TocEntrySpacingRule,
    TocTitleRule,
)
from thesis_review.uno_session import UnoSession


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


def check_doc(path: Path):
    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))
    rules = [TocTitleRule(), TocEntrySpacingRule(), TocEntryFormatRule()]
    return [issue for rule in rules for issue in rule.check(model)]


@pytest.mark.uno
def test_toc_rules_accept_clean_docx():
    issues = check_doc(DOCS / "无误版.docx")

    assert [
        issue for issue in issues
        if issue.rule_id in {"C001", "C002", "C003"}
    ] == []


@pytest.mark.uno
@pytest.mark.parametrize(
    ("filename", "expected_rule"),
    [
        ("C001-1.docx", "C001"),
        ("C001-2.docx", "C001"),
        ("C002-1.docx", "C002"),
        ("C002-2.docx", "C002"),
        ("C003.docx", "C003"),
    ],
)
def test_toc_rules_flag_rule_samples(filename: str, expected_rule: str):
    issues = check_doc(DOCS / "rule" / "C" / filename)

    assert expected_rule in {issue.rule_id for issue in issues}
