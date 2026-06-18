from pathlib import Path

from thesis_review.rules.catalog import load_rule_catalog
from thesis_review.rules.context import RuleContext, build_rule_context
from thesis_review.rules.issue_factory import IssueFactory
from tests.builders import make_doc, make_para


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_build_rule_context_contains_shared_dependencies():
    document = make_doc([
        make_para(flow_index=0, text="目    录"),
        make_para(flow_index=1, text="", runs=[]),
        make_para(flow_index=2, text="第一章  引言\t1"),
    ])
    context = build_rule_context(
        document,
        rules_root=repo_root() / "docs" / "rules",
    )

    assert isinstance(context, RuleContext)
    assert "table-of-contents" in context.sections
    assert context.catalog.get("table-of-contents-title-006").expected == "1 个空段落"
    assert isinstance(context.issue_factory, IssueFactory)


def test_rule_context_can_be_constructed_for_unit_tests():
    document = make_doc([])
    catalog = load_rule_catalog(repo_root() / "docs" / "rules")
    factory = IssueFactory(catalog)
    context = RuleContext(
        document=document,
        sections={},
        catalog=catalog,
        issue_factory=factory,
    )

    assert context.document is document
    assert context.sections == {}
