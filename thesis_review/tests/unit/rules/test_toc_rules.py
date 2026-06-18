"""目录模块规则测试。"""
from __future__ import annotations

from pathlib import Path

from thesis_review.rules.context import build_rule_context
from thesis_review.rules.toc_rules import TableOfContentsEntryChecker
from thesis_review.rules.toc_rules import TableOfContentsTitleChecker
from tests.support.model_builders import make_doc, make_para, make_run


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


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


def test_title_checker_passes_when_title_and_single_blank_are_valid():
    doc = make_doc([toc_title(), empty_para(), toc_entry()])

    assert TableOfContentsTitleChecker().check(context_for(doc)) == []


def test_title_checker_flags_missing_toc_title():
    doc = make_doc([make_para(text="第一章 引言")])

    issues = TableOfContentsTitleChecker().check(context_for(doc))

    assert len(issues) == 1
    assert issues[0].rule_id == "table-of-contents-title-001"
    assert issues[0].actual == "未找到目录"


def test_title_checker_flags_title_text_spacing():
    doc = make_doc([toc_title(text="目  录"), empty_para(), toc_entry()])

    issues = TableOfContentsTitleChecker().check(context_for(doc))

    assert any(
        issue.rule_id == "table-of-contents-title-001"
        and issue.expected == "目    录"
        for issue in issues
    )


def test_title_checker_flags_wrong_title_format():
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

    issues = TableOfContentsTitleChecker().check(context_for(doc))

    assert {issue.rule_id for issue in issues} >= {
        "table-of-contents-title-002",
        "table-of-contents-title-003",
        "table-of-contents-title-004",
        "table-of-contents-title-005",
    }
    assert {issue.actual for issue in issues} >= {
        "左对齐",
        "1 倍",
        "仿宋",
        "14pt",
    }


def test_title_checker_requires_exactly_one_blank_after_title():
    no_blank = make_doc([toc_title(), toc_entry(flow_index=1)])
    too_many = make_doc([
        toc_title(),
        empty_para(1),
        empty_para(2),
        toc_entry(flow_index=3),
    ])

    assert any(
        issue.rule_id == "table-of-contents-title-006"
        and issue.actual == "0 个空段落"
        for issue in TableOfContentsTitleChecker().check(context_for(no_blank))
    )
    assert any(
        issue.rule_id == "table-of-contents-title-006"
        and issue.actual == "2 个空段落"
        for issue in TableOfContentsTitleChecker().check(context_for(too_many))
    )


def doc_with_entries(*entries: str):
    blocks = [toc_title(), empty_para()]
    for offset, text in enumerate(entries, start=2):
        blocks.append(toc_entry(flow_index=offset, text=text))
    blocks.append(make_para(flow_index=len(blocks), text="第一章  引言", outline_level=0))
    return make_doc(blocks)


def test_entry_checker_accepts_required_spacing():
    doc = doc_with_entries(
        "第一章  引言\t1",
        "2.1 线性表的定义\t2",
        "2.2.1 三级标题名\t3",
    )

    assert TableOfContentsEntryChecker().check(context_for(doc)) == []


def test_entry_checker_flags_first_level_spacing():
    doc = doc_with_entries("第一章 引言\t1", "第二章线性表\t2", "第三章   设计\t3")

    issues = TableOfContentsEntryChecker().check(context_for(doc))

    assert len(issues) == 3
    assert all(issue.rule_id == "table-of-contents-entry-001" for issue in issues)


def test_entry_checker_flags_second_and_third_level_spacing():
    doc = doc_with_entries("2.1线性表的定义\t2", "2.2  线性顺序表\t3", "2.2.1三级标题名\t4")

    issues = TableOfContentsEntryChecker().check(context_for(doc))

    assert len(issues) == 3
    assert {issue.rule_id for issue in issues} == {
        "table-of-contents-entry-002",
        "table-of-contents-entry-003",
    }
    assert {issue.actual for issue in issues} >= {"0 个空格", "2 个空格"}


def test_entry_checker_accepts_valid_toc_entry_format():
    doc = doc_with_entries("第一章  引言\t1", "2.1 线性表的定义\t2")

    assert TableOfContentsEntryChecker().check(context_for(doc)) == []


def test_entry_checker_flags_entry_line_spacing_and_bold():
    bad = make_para(
        flow_index=2,
        text="第一章  引言\t1",
        line_spacing=1.0,
        runs=[
            make_run(
                text="第一章  引言\t1",
                font_east_asian="宋体",
                font_latin="Times New Roman",
                size_pt=12.0,
                bold=True,
            )
        ],
    )
    doc = make_doc([
        toc_title(),
        empty_para(),
        bad,
        make_para(flow_index=3, text="第一章  引言", outline_level=0),
    ])

    issues = TableOfContentsEntryChecker().check(context_for(doc))

    assert any(
        issue.rule_id == "table-of-contents-entry-007"
        and issue.actual == "1 倍"
        for issue in issues
    )
    assert any(
        issue.rule_id == "table-of-contents-entry-008"
        and issue.actual == "加粗"
        for issue in issues
    )


def test_entry_checker_flags_entry_run_font_and_size():
    bad = make_para(
        flow_index=2,
        text="第二章  线性表的基本理论知识\t2",
        runs=[
            make_run(
                text="第二章  线性表",
                font_east_asian="宋体",
                font_latin="Times New Roman",
                size_pt=12.0,
            ),
            make_run(
                text="的基本理",
                font_east_asian="仿宋",
                font_latin="仿宋",
                size_pt=12.0,
            ),
            make_run(
                text="论知识\t2",
                font_east_asian="宋体",
                font_latin="Arial",
                size_pt=14.0,
            ),
        ],
    )
    doc = make_doc([
        toc_title(),
        empty_para(),
        bad,
        make_para(flow_index=3, text="第一章  引言", outline_level=0),
    ])

    issues = TableOfContentsEntryChecker().check(context_for(doc))

    assert any(
        issue.rule_id == "table-of-contents-entry-004"
        and issue.expected == "宋体"
        and issue.actual == "仿宋"
        for issue in issues
    )
    assert any(
        issue.rule_id == "table-of-contents-entry-005"
        and issue.expected == "Times New Roman"
        and issue.actual == "Arial"
        for issue in issues
    )
    assert any(
        issue.rule_id == "table-of-contents-entry-006"
        and issue.expected == "小四（12pt）"
        and issue.actual == "14pt"
        for issue in issues
    )


def test_entry_checker_skips_when_table_of_contents_section_missing():
    doc = make_doc([
        make_para(flow_index=0, text="第一章  引言\t1"),
        make_para(flow_index=1, text="正文段落"),
    ])

    issues = TableOfContentsEntryChecker().check(context_for(doc))

    assert issues == []
