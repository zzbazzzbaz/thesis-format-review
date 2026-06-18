from thesis_review.rules.base import RuleChecker


class DummyChecker:
    checker_id = "dummy"
    rule_ids = ("table-of-contents-title-006",)

    def check(self, context):
        return []


def test_checker_protocol_accepts_duck_type():
    assert isinstance(DummyChecker(), RuleChecker)
