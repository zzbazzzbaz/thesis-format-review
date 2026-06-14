from thesis_review.rules.base import Rule
from thesis_review.rules.registry import get_rules


def test_registry_returns_all_six_rules():
    rules = get_rules()
    ids = {rule.rule_id for rule in rules}
    assert ids == {
        "format.body.font",
        "format.body.size",
        "format.body.line_spacing",
        "format.body.indent",
        "structure.heading.hierarchy",
        "structure.section.required",
    }


def test_registry_rules_satisfy_protocol():
    for rule in get_rules():
        assert isinstance(rule, Rule)


def test_registry_returns_fresh_rule_list():
    rules = get_rules()
    rules.clear()

    assert len(get_rules()) == 6
