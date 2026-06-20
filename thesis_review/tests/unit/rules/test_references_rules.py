from pathlib import Path

from thesis_review.rules.context import build_rule_context
from thesis_review.rules.references_rules import ReferencesEntryChecker, ReferencesTitleChecker
from tests.support.model_builders import make_doc, make_para, make_run


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def run(text, east="宋体", latin="Times New Roman", size=12.0):
    return make_run(text=text, font_east_asian=east, font_latin=latin, size_pt=size)


def empty(flow_index):
    return make_para(flow_index=flow_index, text="", runs=[])


def references_doc(*ref_paras):
    return make_doc([
        make_para(flow_index=0, text="第一章  引言"),
        *ref_paras,
        make_para(flow_index=len(ref_paras) + 1, text="致    谢"),
    ])


def title(flow_index=1, text="参考文献"):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment="center",
        first_line_indent_chars=0.0,
        runs=[run(text)],
    )


def entry(
    flow_index=3,
    text="[1] 严蔚敏. Data 2026.",
    east="宋体",
    latin="Times New Roman",
    size=12.0,
    line_spacing=1.5,
):
    return make_para(
        flow_index=flow_index,
        text=text,
        line_spacing=line_spacing,
        first_line_indent_chars=0.0,
        runs=[
            run("[1] ", east=east, latin=latin, size=size),
            run("严蔚敏. ", east=east, latin=latin, size=size),
            run("Data 2026.", east=east, latin=latin, size=size),
        ],
    )


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def test_references_title_checker_accepts_valid_title_and_blank():
    doc = references_doc(title(1), empty(2), entry(3))

    assert ReferencesTitleChecker().check(context_for(doc)) == []


def test_references_title_checker_flags_text_and_blank_count():
    doc = references_doc(title(1, text="参考 文献"), entry(2))

    issues = ReferencesTitleChecker().check(context_for(doc))

    assert rule_ids(issues) == {"references-title-001", "references-title-002"}


def test_references_entry_checker_accepts_valid_entry():
    doc = references_doc(title(1), empty(2), entry(3))

    assert ReferencesEntryChecker().check(context_for(doc)) == []


def test_references_entry_checker_flags_numbering_and_spacing():
    bad_number = make_para(
        flow_index=3,
        text="1.严蔚敏. Data.",
        runs=[run("1.严蔚敏. Data.")],
    )
    bad_space = make_para(
        flow_index=4,
        text="[2]  王伟国. Data.",
        runs=[run("[2]  王伟国. Data.")],
    )
    doc = references_doc(title(1), empty(2), bad_number, bad_space)

    issues = ReferencesEntryChecker().check(context_for(doc))

    assert rule_ids(issues) >= {"references-entry-001", "references-entry-002"}


def test_references_entry_checker_flags_format_rules():
    doc = references_doc(
        title(1),
        empty(2),
        entry(3, east="仿宋", latin="Arial", size=10.5, line_spacing=1.0),
    )

    issues = ReferencesEntryChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "references-entry-003",
        "references-entry-004",
        "references-entry-005",
        "references-entry-006",
    }
