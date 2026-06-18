import pytest

from thesis_review.core.models import Location
from thesis_review.rules.catalog import RuleCatalog, RuleSpec
from thesis_review.rules.issue_factory import IssueFactory, UnknownRuleIdError


def make_catalog() -> RuleCatalog:
    rule = RuleSpec(
        id="table-of-contents-title-006",
        title="目录标题后空行",
        severity="error",
        status="active",
        description="检查目录标题后空行。",
        message="目录标题后必须且只能空一行",
        expected="1 个空段落",
    )
    return RuleCatalog(
        rules_by_id={rule.id: rule},
        modules_by_name={},
    )


def make_location() -> Location:
    return Location(
        target="block",
        block_id="b-0000",
        block_kind="paragraph",
        flow_index=0,
    )


def test_issue_factory_fills_fields_from_catalog():
    issue = IssueFactory(make_catalog()).create(
        rule_id="table-of-contents-title-006",
        actual="0 个空段落",
        location=make_location(),
    )

    assert issue.rule_id == "table-of-contents-title-006"
    assert issue.category == "format"
    assert issue.severity == "error"
    assert issue.message == "目录标题后必须且只能空一行"
    assert issue.expected == "1 个空段落"
    assert issue.actual == "0 个空段落"


def test_issue_factory_rejects_unknown_rule_id():
    factory = IssueFactory(make_catalog())

    with pytest.raises(UnknownRuleIdError, match="unknown-rule-id"):
        factory.create(
            rule_id="unknown-rule-id",
            actual="实际值",
            location=make_location(),
        )
