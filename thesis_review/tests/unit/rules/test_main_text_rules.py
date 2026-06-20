from pathlib import Path

from thesis_review.rules.context import build_rule_context
from thesis_review.rules.main_text_rules import (
    MainTextHeadingChecker,
    MainTextParagraphChecker,
    MainTextReferenceCitationChecker,
)
from tests.support.model_builders import make_doc, make_para, make_run


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def run(
    text,
    east="宋体",
    latin="Times New Roman",
    size=12.0,
    bold=False,
    superscript=False,
):
    return make_run(
        text=text,
        font_east_asian=east,
        font_latin=latin,
        size_pt=size,
        bold=bold,
        superscript=superscript,
    )


def thesis_doc(*main_paras):
    return make_doc([
        make_para(flow_index=0, text="摘    要"),
        make_para(flow_index=1, text="摘要正文"),
        make_para(flow_index=2, text="目    录"),
        make_para(flow_index=3, text="", runs=[]),
        make_para(flow_index=4, text="第一章  引言\t1"),
        *main_paras,
        make_para(flow_index=4 + len(main_paras) + 1, text="参考文献"),
    ])


def h1(flow_index=5, text="第一章  引言", east="黑体", size=16.0, page_break_before=True):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment="center",
        first_line_indent_chars=0.0,
        page_break_before=page_break_before,
        runs=[run(text, east=east, latin="Times New Roman", size=size)],
    )


def h2(
    flow_index=7,
    text="2.1 线性表的定义",
    east="黑体",
    latin="Times New Roman",
    size=14.0,
    line_spacing=1.5,
):
    return make_para(
        flow_index=flow_index,
        text=text,
        line_spacing=line_spacing,
        first_line_indent_chars=0.0,
        runs=[
            run(text[:3], east=east, latin=latin, size=size),
            run(text[3:], east=east, latin=latin, size=size),
        ],
    )


def h3(
    flow_index=8,
    text="2.1.1 三级标题",
    east="黑体",
    latin="Times New Roman",
    size=12.0,
    line_spacing=1.5,
    indent=2.0,
):
    return make_para(
        flow_index=flow_index,
        text=text,
        line_spacing=line_spacing,
        first_line_indent_chars=indent,
        runs=[
            run(text[:5], east=east, latin=latin, size=size),
            run(text[5:], east=east, latin=latin, size=size),
        ],
    )


def empty(flow_index):
    return make_para(flow_index=flow_index, text="", runs=[])


def body(flow_index=9):
    return make_para(
        flow_index=flow_index,
        text="正文段落。",
        alignment="justify",
        line_spacing=1.5,
        first_line_indent_chars=2.0,
        runs=[run("正文段落。")],
    )


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def test_main_text_heading_checker_accepts_valid_headings():
    doc = thesis_doc(h1(5), empty(6), h2(7), h3(8), body(9))

    assert MainTextHeadingChecker().check(context_for(doc)) == []


def test_main_text_heading_checker_flags_level_one_rules():
    doc = thesis_doc(
        h1(5, text="第2章 引言", east="宋体", size=12.0, page_break_before=False),
        body(6),
    )

    issues = MainTextHeadingChecker().check(context_for(doc))

    assert rule_ids(issues) >= {
        "main-text-heading-level-one-001",
        "main-text-heading-level-one-002",
        "main-text-heading-level-one-003",
        "main-text-heading-level-one-004",
        "main-text-heading-level-one-005",
        "main-text-heading-level-one-006",
    }


def test_main_text_heading_checker_flags_level_two_rules():
    doc = thesis_doc(
        h1(5),
        empty(6),
        h2(
            7,
            text="22 线性顺序表",
            east="宋体",
            latin="Arial",
            size=12.0,
            line_spacing=1.0,
        ),
    )

    issues = MainTextHeadingChecker().check(context_for(doc))

    assert rule_ids(issues) >= {
        "main-text-heading-level-two-001",
        "main-text-heading-level-two-002",
        "main-text-heading-level-two-003",
        "main-text-heading-level-two-004",
        "main-text-heading-level-two-005",
        "main-text-heading-level-two-006",
    }


def test_main_text_heading_checker_flags_level_three_rules():
    doc = thesis_doc(
        h1(5),
        empty(6),
        h3(
            7,
            text="2.11三级标题",
            east="宋体",
            latin="Arial",
            size=10.5,
            line_spacing=1.0,
            indent=0.0,
        ),
    )

    issues = MainTextHeadingChecker().check(context_for(doc))

    assert rule_ids(issues) >= {
        "main-text-heading-level-three-001",
        "main-text-heading-level-three-002",
        "main-text-heading-level-three-003",
        "main-text-heading-level-three-004",
        "main-text-heading-level-three-005",
        "main-text-heading-level-three-006",
        "main-text-heading-level-three-007",
    }
