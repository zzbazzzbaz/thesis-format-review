"""摘要模块规则测试。"""
from __future__ import annotations

from pathlib import Path

from thesis_review.rules.abstract_rules import AbstractChineseKeywordsChecker
from thesis_review.rules.abstract_rules import AbstractChineseTitleBodyChecker
from thesis_review.rules.abstract_rules import AbstractEnglishKeywordsChecker
from thesis_review.rules.abstract_rules import AbstractEnglishTitleBodyChecker
from thesis_review.rules.context import build_rule_context
from tests.support.model_builders import make_doc, make_para, make_run


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def run(
    text: str,
    east: str = "宋体",
    latin: str = "Times New Roman",
    size: float = 12.0,
    bold: bool = False,
):
    return make_run(
        text=text,
        font_east_asian=east,
        font_latin=latin,
        size_pt=size,
        bold=bold,
    )


def empty(flow_index: int):
    return make_para(flow_index=flow_index, text="", runs=[])


def chinese_title(
    flow_index: int = 1,
    text: str = "摘    要",
    font: str = "黑体",
    size: float = 16.0,
):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment="center",
        line_spacing=1.5,
        first_line_indent_chars=0.0,
        runs=[run(text, east=font, latin=font, size=size)],
    )


def chinese_body(
    flow_index: int = 3,
    text: str = "中文摘要正文",
    font: str = "宋体",
    size: float = 12.0,
    line_spacing: float | None = 1.5,
    indent: float | None = 2.0,
):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment="justify",
        line_spacing=line_spacing,
        first_line_indent_chars=indent,
        runs=[run(text, east=font, latin="Times New Roman", size=size)],
    )


def chinese_keywords(flow_index: int = 5):
    return make_para(
        flow_index=flow_index,
        text="关键词：毕业设计；格式；规范",
        alignment="justify",
        line_spacing=1.5,
        first_line_indent_chars=2.0,
        runs=[
            run("关键词：", east="宋体", size=12.0, bold=True),
            run("毕业设计；格式；规范", east="宋体", latin="宋体", size=12.0),
        ],
    )


def english_title(flow_index: int = 6):
    return make_para(
        flow_index=flow_index,
        text="ABSTRACT",
        alignment="center",
        line_spacing=1.5,
        first_line_indent_chars=0.0,
        runs=[run("ABSTRACT", east="宋体", latin="Times New Roman", size=16.0, bold=True)],
    )


def english_body(
    flow_index: int = 8,
    text: str = "English abstract body.",
    east: str = "宋体",
    latin: str = "Times New Roman",
    size: float = 12.0,
    line_spacing: float | None = 1.5,
    indent: float | None = 2.0,
):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment="justify",
        line_spacing=line_spacing,
        first_line_indent_chars=indent,
        runs=[run(text, east=east, latin=latin, size=size)],
    )


def english_keywords(flow_index: int = 10):
    return make_para(
        flow_index=flow_index,
        text="Keywords：Data；Format；Rule",
        alignment="justify",
        line_spacing=1.5,
        first_line_indent_chars=2.0,
        runs=[
            run("Keywords：", east="宋体", latin="Times New Roman", size=12.0, bold=True),
            run("Data；Format；Rule", east="宋体", latin="Times New Roman", size=12.0),
        ],
    )


def valid_chinese_doc():
    return make_doc([
        make_para(flow_index=0, text="封面"),
        chinese_title(1),
        empty(2),
        chinese_body(3),
        empty(4),
        chinese_keywords(5),
        english_title(6),
        empty(7),
        english_body(8),
        empty(9),
        english_keywords(10),
        make_para(flow_index=11, text="目    录"),
    ])


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def test_chinese_title_body_checker_accepts_valid_format():
    doc = valid_chinese_doc()

    assert AbstractChineseTitleBodyChecker().check(context_for(doc)) == []


def test_chinese_title_body_checker_flags_case_rules():
    doc = make_doc([
        make_para(flow_index=0, text="封面"),
        chinese_title(1, text="摘   要", font="仿宋", size=15.0),
        empty(2),
        empty(3),
        chinese_body(
            4,
            font="仿宋",
            size=10.5,
            line_spacing=1.0,
            indent=1.5,
        ),
        chinese_keywords(5),
        english_title(6),
        make_para(flow_index=7, text="目    录"),
    ])

    issues = AbstractChineseTitleBodyChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "abstract-chinese-title-001",
        "abstract-chinese-title-002",
        "abstract-chinese-title-003",
        "abstract-chinese-title-005",
        "abstract-chinese-body-001",
        "abstract-chinese-body-002",
        "abstract-chinese-body-004",
        "abstract-chinese-body-005",
        "abstract-chinese-body-006",
    }


def test_chinese_keywords_checker_accepts_valid_format():
    doc = valid_chinese_doc()

    assert AbstractChineseKeywordsChecker().check(context_for(doc)) == []


def test_chinese_keywords_checker_flags_case_rules():
    bad_keywords = make_para(
        flow_index=5,
        text="关键词:毕业设计；格式;规范；",
        alignment="justify",
        line_spacing=1.5,
        first_line_indent_chars=2.0,
        runs=[
            run("关", east="仿宋", latin="仿宋", size=12.0, bold=False),
            run("键", east="宋体", latin="Times New Roman", size=10.5, bold=True),
            run("词", east="宋体", latin="Times New Roman", size=12.0, bold=True),
            run(":", east="宋体", latin="Times New Roman", size=12.0, bold=True),
            run("毕业设计；格式", east="宋体", latin="宋体", size=12.0),
            run(";", east="宋体", latin="宋体", size=12.0),
            run("规范", east="宋体", latin="宋体", size=12.0),
            run("；", east="宋体", latin="宋体", size=12.0),
        ],
    )
    doc = make_doc([
        make_para(flow_index=0, text="封面"),
        chinese_title(1),
        empty(2),
        chinese_body(3),
        empty(4),
        bad_keywords,
        english_title(6),
        make_para(flow_index=7, text="目    录"),
    ])

    issues = AbstractChineseKeywordsChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "abstract-chinese-keywords-001",
        "abstract-chinese-keywords-002",
        "abstract-chinese-keywords-003",
        "abstract-chinese-keywords-004",
        "abstract-chinese-keywords-005",
        "abstract-chinese-keywords-006",
    }


def test_english_title_body_checker_accepts_valid_format():
    doc = valid_chinese_doc()

    assert AbstractEnglishTitleBodyChecker().check(context_for(doc)) == []


def test_english_title_body_checker_flags_case_rules():
    bad_title = make_para(
        flow_index=6,
        text="ABSTRAcT",
        alignment="left",
        line_spacing=1.5,
        first_line_indent_chars=1.5,
        runs=[run("ABSTRAcT", east="仿宋", latin="仿宋", size=14.0, bold=False)],
    )
    bad_body = english_body(
        7,
        east="仿宋",
        latin="仿宋",
        size=14.0,
        line_spacing=1.0,
        indent=2.5,
    )
    doc = make_doc([
        make_para(flow_index=0, text="封面"),
        chinese_title(1),
        empty(2),
        chinese_body(3),
        empty(4),
        chinese_keywords(5),
        bad_title,
        bad_body,
        empty(8),
        empty(9),
        english_keywords(10),
        make_para(flow_index=11, text="目    录"),
    ])

    issues = AbstractEnglishTitleBodyChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "abstract-english-title-001",
        "abstract-english-title-002",
        "abstract-english-title-003",
        "abstract-english-title-004",
        "abstract-english-title-005",
        "abstract-english-title-006",
        "abstract-english-body-001",
        "abstract-english-body-002",
        "abstract-english-body-003",
        "abstract-english-body-004",
        "abstract-english-body-005",
    }


def test_english_keywords_checker_accepts_valid_format_with_songti_punctuation():
    doc = make_doc([
        make_para(flow_index=0, text="封面"),
        chinese_title(1),
        empty(2),
        chinese_body(3),
        empty(4),
        chinese_keywords(5),
        english_title(6),
        empty(7),
        english_body(8),
        empty(9),
        make_para(
            flow_index=10,
            text="Keywords：Data；Format；Rule",
            alignment="justify",
            line_spacing=1.5,
            first_line_indent_chars=2.0,
            runs=[
                run("Keywords", east="宋体", latin="Times New Roman", size=12.0, bold=True),
                run("：", east="宋体", latin="宋体", size=12.0, bold=True),
                run("Data", east="宋体", latin="Times New Roman", size=12.0),
                run("；", east="宋体", latin="宋体", size=12.0),
                run("Format", east="宋体", latin="Times New Roman", size=12.0),
                run("；", east="宋体", latin="宋体", size=12.0),
                run("Rule", east="宋体", latin="Times New Roman", size=12.0),
            ],
        ),
        make_para(flow_index=11, text="目    录"),
    ])

    assert AbstractEnglishKeywordsChecker().check(context_for(doc)) == []


def test_english_keywords_checker_flags_case_rules():
    bad_keywords = make_para(
        flow_index=10,
        text="Keywords:Xxxx；Xxxx;Xxxx;",
        alignment="justify",
        line_spacing=2.0,
        first_line_indent_chars=1.5,
        runs=[
            run("Ke", east="宋体", latin="Times New Roman", size=12.0, bold=True),
            run("yw", east="宋体", latin="Times New Roman", size=12.0, bold=False),
            run("ord", east="宋体", latin="Times New Roman", size=10.5, bold=True),
            run("s", east="宋体", latin="Times New Roman", size=12.0, bold=True),
            run(":", east="宋体", latin="Times New Roman", size=12.0, bold=True),
            run("Xxxx；X", east="宋体", latin="Times New Roman", size=12.0),
            run("xx", east="仿宋", latin="仿宋", size=12.0),
            run("x", east="宋体", latin="Times New Roman", size=12.0),
            run(";", east="宋体", latin="Times New Roman", size=12.0),
            run("Xxxx", east="宋体", latin="Times New Roman", size=12.0),
            run(";", east="宋体", latin="Times New Roman", size=12.0),
        ],
    )
    doc = make_doc([
        make_para(flow_index=0, text="封面"),
        chinese_title(1),
        empty(2),
        chinese_body(3),
        empty(4),
        chinese_keywords(5),
        english_title(6),
        empty(7),
        english_body(8),
        empty(9),
        bad_keywords,
        make_para(flow_index=11, text="目    录"),
    ])

    issues = AbstractEnglishKeywordsChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "abstract-english-keywords-001",
        "abstract-english-keywords-002",
        "abstract-english-keywords-003",
        "abstract-english-keywords-004",
        "abstract-english-keywords-005",
        "abstract-english-keywords-006",
        "abstract-english-keywords-007",
        "abstract-english-keywords-008",
    }
