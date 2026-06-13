from src.rules.structure_rules import HeadingHierarchyRule
from src.rules.structure_rules import RequiredSectionRule
from tests.builders import make_doc, make_para


def test_hierarchy_ok_when_sequential():
    doc = make_doc(
        [
            make_para(paragraph_index=0, outline_level=0, text="第一章"),
            make_para(paragraph_index=1, outline_level=1, text="1.1 节"),
            make_para(paragraph_index=2, outline_level=2, text="1.1.1 小节"),
        ]
    )
    assert HeadingHierarchyRule().check(doc) == []


def test_hierarchy_flags_skip():
    doc = make_doc(
        [
            make_para(paragraph_index=0, outline_level=0, text="第一章"),
            make_para(paragraph_index=1, outline_level=2, text="1.1.1 小节"),
        ]
    )
    issues = HeadingHierarchyRule().check(doc)
    assert len(issues) == 1
    assert issues[0].rule_id == "structure.heading.hierarchy"
    assert issues[0].location.paragraph_index == 1


def test_hierarchy_ignores_body_paragraphs():
    doc = make_doc(
        [
            make_para(paragraph_index=0, outline_level=0, text="第一章"),
            make_para(paragraph_index=1, outline_level=None, text="正文段落"),
            make_para(paragraph_index=2, outline_level=1, text="1.1 节"),
        ]
    )
    assert HeadingHierarchyRule().check(doc) == []


def test_required_sections_all_present():
    doc = make_doc(
        [
            make_para(paragraph_index=0, outline_level=0, text="摘要"),
            make_para(paragraph_index=1, outline_level=0, text="关键词"),
            make_para(paragraph_index=2, outline_level=0, text="参考文献"),
        ]
    )
    assert RequiredSectionRule().check(doc) == []


def test_required_sections_missing_one():
    doc = make_doc(
        [
            make_para(paragraph_index=0, outline_level=0, text="摘要"),
            make_para(paragraph_index=1, outline_level=0, text="关键词"),
        ]
    )
    issues = RequiredSectionRule().check(doc)
    assert len(issues) == 1
    assert issues[0].rule_id == "structure.section.required"
    assert "参考文献" in issues[0].message
    assert issues[0].location.paragraph_index == 0


def test_required_sections_matches_substring():
    doc = make_doc(
        [
            make_para(paragraph_index=0, outline_level=0, text="摘  要"),
            make_para(paragraph_index=1, outline_level=0, text="关键词："),
            make_para(paragraph_index=2, outline_level=0, text="参考文献"),
        ]
    )
    assert RequiredSectionRule().check(doc) == []
