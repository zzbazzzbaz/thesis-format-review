from thesis_review.rules.base import RuleChecker
from thesis_review.rules.registry import get_checkers


def test_registry_returns_all_checkers():
    checkers = get_checkers()
    ids = {checker.checker_id for checker in checkers}
    assert ids == {
        "abstract-chinese-title-body",
        "abstract-chinese-keywords",
        "abstract-english-title-body",
        "abstract-english-keywords",
        "table-of-contents-title",
        "table-of-contents-entry",
    }


def test_registry_checkers_satisfy_protocol():
    for checker in get_checkers():
        assert isinstance(checker, RuleChecker)


def test_registry_returns_fresh_checker_list():
    checkers = get_checkers()
    checkers.clear()

    assert len(get_checkers()) == 6


def test_registry_includes_table_of_contents_rule_ids():
    rule_ids = {rule_id for checker in get_checkers() for rule_id in checker.rule_ids}

    assert "table-of-contents-title-006" in rule_ids
    assert "table-of-contents-entry-008" in rule_ids


def test_registry_includes_abstract_rule_ids():
    rule_ids = {rule_id for checker in get_checkers() for rule_id in checker.rule_ids}

    assert "abstract-chinese-title-001" in rule_ids
    assert "abstract-chinese-body-006" in rule_ids
    assert "abstract-chinese-keywords-006" in rule_ids
    assert "abstract-english-title-006" in rule_ids
    assert "abstract-english-body-005" in rule_ids
    assert "abstract-english-keywords-008" in rule_ids
