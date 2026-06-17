from thesis_review.rules.base import Rule
from thesis_review.rules.registry import get_rules


def test_registry_returns_all_rules():
    rules = get_rules()
    ids = {rule.rule_id for rule in rules}
    assert ids == {
        "C001",
        "C002",
        "C003",
    }


def test_registry_rules_satisfy_protocol():
    for rule in get_rules():
        assert isinstance(rule, Rule)


def test_registry_returns_fresh_rule_list():
    rules = get_rules()
    rules.clear()

    assert len(get_rules()) == 3


def test_registry_includes_toc_business_rules():
    rule_ids = {rule.rule_id for rule in get_rules()}

    assert {"C001", "C002", "C003"} <= rule_ids
