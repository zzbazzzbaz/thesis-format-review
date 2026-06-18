from thesis_review.rules.base import RuleChecker
from thesis_review.rules.registry import get_checkers


def test_registry_returns_all_checkers():
    checkers = get_checkers()
    ids = {checker.checker_id for checker in checkers}
    assert ids == {
        "table-of-contents-title",
        "table-of-contents-entry",
    }


def test_registry_checkers_satisfy_protocol():
    for checker in get_checkers():
        assert isinstance(checker, RuleChecker)


def test_registry_returns_fresh_checker_list():
    checkers = get_checkers()
    checkers.clear()

    assert len(get_checkers()) == 2


def test_registry_includes_table_of_contents_rule_ids():
    rule_ids = {rule_id for checker in get_checkers() for rule_id in checker.rule_ids}

    assert "table-of-contents-title-006" in rule_ids
    assert "table-of-contents-entry-008" in rule_ids
