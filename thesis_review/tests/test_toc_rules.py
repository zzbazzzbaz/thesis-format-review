"""目录 C 类规则测试。"""
from __future__ import annotations

from thesis_review.rules.toc_rules import TocTitleRule
from tests.builders import make_doc, make_para, make_run


def toc_title(
    text="目    录",
    alignment="center",
    line_spacing=1.5,
    font="黑体",
    size=16.0,
):
    return make_para(
        flow_index=0,
        text=text,
        alignment=alignment,
        line_spacing=line_spacing,
        first_line_indent_chars=0.0,
        runs=[
            make_run(
                text=text,
                font_east_asian=font,
                font_latin="Times New Roman",
                size_pt=size,
            )
        ],
    )


def empty_para(flow_index=1):
    return make_para(flow_index=flow_index, text="", runs=[])


def toc_entry(flow_index=2, text="第一章  引言\t1"):
    return make_para(
        flow_index=flow_index,
        text=text,
        first_line_indent_chars=0.0,
        runs=[
            make_run(
                text=text,
                font_east_asian="宋体",
                font_latin="Times New Roman",
                size_pt=12.0,
            )
        ],
    )


def test_c001_passes_when_title_and_single_blank_are_valid():
    doc = make_doc([toc_title(), empty_para(), toc_entry()])

    assert TocTitleRule().check(doc) == []


def test_c001_flags_missing_toc_title():
    doc = make_doc([make_para(text="第一章 引言")])

    issues = TocTitleRule().check(doc)

    assert len(issues) == 1
    assert issues[0].rule_id == "C001"
    assert "缺少目录标题" in issues[0].message


def test_c001_flags_title_text_spacing():
    doc = make_doc([toc_title(text="目  录"), empty_para(), toc_entry()])

    issues = TocTitleRule().check(doc)

    assert any(
        issue.rule_id == "C001" and issue.expected == "目    录"
        for issue in issues
    )


def test_c001_flags_wrong_title_format():
    doc = make_doc([
        toc_title(
            alignment="left",
            line_spacing=1.0,
            font="仿宋",
            size=14.0,
        ),
        empty_para(),
        toc_entry(),
    ])

    issues = TocTitleRule().check(doc)

    assert {issue.actual for issue in issues} >= {
        "left",
        "1.0",
        "仿宋",
        "14.0",
    }


def test_c001_requires_exactly_one_blank_after_title():
    no_blank = make_doc([toc_title(), toc_entry(flow_index=1)])
    too_many = make_doc([
        toc_title(),
        empty_para(1),
        empty_para(2),
        toc_entry(flow_index=3),
    ])

    assert any("空一行" in issue.message for issue in TocTitleRule().check(no_blank))
    assert any(
        "只能空一行" in issue.message
        for issue in TocTitleRule().check(too_many)
    )
