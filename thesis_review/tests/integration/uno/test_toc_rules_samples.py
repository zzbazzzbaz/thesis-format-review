"""目录规则真实 Word 样本测试。"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("uno")

from thesis_review.adapters.uno.extractor import extract
from thesis_review.rules.catalog import (
    RuleCatalogError,
    load_rule_catalog,
    load_rule_cases,
)
from thesis_review.rules.context import build_rule_context
from thesis_review.rules.registry import get_checkers
from thesis_review.adapters.uno.session import UnoSession


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rules_root() -> Path:
    return repo_root() / "docs" / "rules"


def rule_cases():
    try:
        catalog = load_rule_catalog(rules_root())
        return load_rule_cases(rules_root(), catalog)
    except RuleCatalogError as exc:
        pytest.skip(f"目录规则 Word 样本未准备完整：{exc}", allow_module_level=True)


def check_doc(path: Path):
    with UnoSession() as session:
        with session.open(str(path)) as doc:
            model = extract(doc, source_path=str(path))
    context = build_rule_context(model, rules_root=rules_root())
    return [
        issue
        for checker in get_checkers()
        for issue in checker.check(context)
    ]


@pytest.mark.uno
@pytest.mark.parametrize(
    "case",
    rule_cases(),
    ids=lambda case: case.id,
)
def test_table_of_contents_rule_cases(case):
    module_dir = rules_root() / "table-of-contents"
    sample_path = module_dir / case.file
    if not sample_path.exists():
        pytest.skip(f"目录规则 Word 样本未准备：{sample_path}")

    issues = check_doc(sample_path)
    actual_rule_ids = {issue.rule_id for issue in issues}

    assert set(case.expected_rule_ids) <= actual_rule_ids
    if not case.expected_rule_ids:
        assert actual_rule_ids.isdisjoint(
            {
                "table-of-contents-title-001",
                "table-of-contents-title-002",
                "table-of-contents-title-003",
                "table-of-contents-title-004",
                "table-of-contents-title-005",
                "table-of-contents-title-006",
                "table-of-contents-entry-001",
                "table-of-contents-entry-002",
                "table-of-contents-entry-003",
                "table-of-contents-entry-004",
                "table-of-contents-entry-005",
                "table-of-contents-entry-006",
                "table-of-contents-entry-007",
                "table-of-contents-entry-008",
            }
        )
