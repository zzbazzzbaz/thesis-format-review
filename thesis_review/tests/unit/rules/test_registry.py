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
        "cover-title",
        "cover-info",
        "cover-date",
        "references-title",
        "references-entry",
        "acknowledgements-title",
        "acknowledgements-body",
        "appendix-title",
        "appendix-body",
        "main-text-heading",
        "main-text-paragraph",
        "main-text-reference-citation",
    }


def test_registry_checkers_satisfy_protocol():
    for checker in get_checkers():
        assert isinstance(checker, RuleChecker)


def test_registry_returns_fresh_checker_list():
    checkers = get_checkers()
    checkers.clear()

    assert len(get_checkers()) == 18


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


def test_registry_includes_phase_one_rule_ids():
    rule_ids = {rule_id for checker in get_checkers() for rule_id in checker.rule_ids}

    assert "cover-title-001" in rule_ids
    assert "references-entry-006" in rule_ids
    assert "acknowledgements-body-006" in rule_ids
    assert "appendix-body-006" in rule_ids
    assert "main-text-heading-level-three-007" in rule_ids
    assert "main-text-paragraph-006" in rule_ids
    assert "main-text-reference-citation-004" in rule_ids
