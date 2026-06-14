from thesis_review.models import DocumentModel
from thesis_review.rules.base import Rule


def test_rule_protocol_is_satisfied_by_a_simple_rule():
    class DummyRule:
        rule_id = "dummy"
        category = "format"
        severity = "info"

        def check(self, document: DocumentModel):
            return []

    rule: Rule = DummyRule()
    assert rule.rule_id == "dummy"
    assert rule.check(DocumentModel(source_docx="x", paragraphs=[])) == []
