from pathlib import Path

from thesis_review.rules.context import build_rule_context
from thesis_review.rules.cover_rules import (
    CoverDateChecker,
    CoverInfoChecker,
    CoverTitleChecker,
)
from tests.support.model_builders import make_doc, make_para, make_run


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def para(flow_index, text, east="仿宋", size=16.0, bold=True):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment="center",
        first_line_indent_chars=0.0,
        runs=[
            make_run(
                text=text,
                font_east_asian=east,
                font_latin="Times New Roman",
                size_pt=size,
                bold=bold,
            )
        ],
    )


def cover_doc(*cover_paras):
    return make_doc([
        *cover_paras,
        make_para(flow_index=len(cover_paras), text="摘    要"),
        make_para(flow_index=len(cover_paras) + 1, text="摘要正文"),
        make_para(flow_index=len(cover_paras) + 2, text="目    录"),
    ])


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def test_cover_title_checker_accepts_valid_title_line():
    doc = cover_doc(
        make_para(
            flow_index=0,
            text="题    目：线性表的设计和实现",
            alignment="center",
            runs=[
                make_run(
                    text="题    目：",
                    font_east_asian="仿宋",
                    font_latin="Times New Roman",
                    size_pt=16.0,
                    bold=False,
                ),
                make_run(
                    text="线性表的设计和实现",
                    font_east_asian="黑体",
                    font_latin="Times New Roman",
                    size_pt=18.0,
                    bold=False,
                ),
            ],
        )
    )

    assert CoverTitleChecker().check(context_for(doc)) == []


def test_cover_title_checker_flags_label_font_and_size_only():
    doc = cover_doc(
        make_para(
            flow_index=0,
            text="题    目：线性表的设计和实现",
            alignment="center",
            runs=[
                make_run(
                    text="题    目：",
                    font_east_asian="宋体",
                    font_latin="Times New Roman",
                    size_pt=12.0,
                    bold=False,
                ),
                make_run(
                    text="线性表的设计和实现",
                    font_east_asian="黑体",
                    font_latin="Times New Roman",
                    size_pt=18.0,
                    bold=False,
                ),
            ],
        )
    )

    issues = CoverTitleChecker().check(context_for(doc))

    assert rule_ids(issues) == {"cover-title-label-001", "cover-title-label-002"}


def test_cover_title_checker_flags_font_and_size():
    doc = cover_doc(
        make_para(
            flow_index=0,
            text="题    目：线性表的设计和实现",
            alignment="center",
            runs=[
                make_run(
                    text="题    目：",
                    font_east_asian="仿宋",
                    font_latin="Times New Roman",
                    size_pt=16.0,
                    bold=False,
                ),
                make_run(
                    text="线性表的设计和实现",
                    font_east_asian="宋体",
                    font_latin="Times New Roman",
                    size_pt=16.0,
                    bold=False,
                ),
            ],
        )
    )

    issues = CoverTitleChecker().check(context_for(doc))

    assert rule_ids(issues) == {"cover-title-001", "cover-title-002"}


def test_cover_info_checker_flags_info_line_format():
    doc = cover_doc(
        para(0, "学生姓名：张三", east="宋体", size=12.0, bold=False),
        para(1, "学    号：201107011153", east="仿宋", size=16.0, bold=True),
    )

    issues = CoverInfoChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "cover-info-001",
        "cover-info-002",
        "cover-info-003",
    }


def test_cover_date_checker_flags_date_line_format():
    doc = cover_doc(para(0, "2026 年 6 月 20 日", east="宋体", size=12.0, bold=False))

    issues = CoverDateChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "cover-date-001",
        "cover-date-002",
        "cover-date-003",
    }


def test_cover_checkers_do_not_report_missing_objects():
    doc = cover_doc(para(0, "本科生毕业设计（论文）", east="黑体", size=18.0, bold=True))
    context = context_for(doc)

    assert CoverTitleChecker().check(context) == []
    assert CoverInfoChecker().check(context) == []
    assert CoverDateChecker().check(context) == []
