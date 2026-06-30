"""文档分区测试。"""
from __future__ import annotations

from thesis_review.core.sections import detect_sections
from thesis_review.core.sections import norm_text
from thesis_review.core.sections import paragraphs_in_range
from tests.support.model_builders import make_doc, make_para


def test_norm_text_removes_spaces_tabs_and_colons():
    assert norm_text("目    录") == "目录"
    assert norm_text("摘\t 要：") == "摘要"
    assert norm_text("致　　谢") == "致谢"


def test_detect_toc_does_not_treat_toc_first_chapter_as_body_start():
    doc = make_doc([
        make_para(flow_index=0, text="摘 要"),
        make_para(flow_index=1, text="ABSTRACT"),
        make_para(flow_index=2, text="目    录", alignment="center"),
        make_para(flow_index=3, text="", runs=[]),
        make_para(flow_index=4, text="摘要\t1"),
        make_para(flow_index=5, text="ABSTRACT\t2"),
        make_para(flow_index=6, text="第一章  引言\t3"),
        make_para(flow_index=7, text="2.1 线性表的定义\t4"),
        make_para(flow_index=8, text="参考文献\t5"),
        make_para(flow_index=9, text="致谢\t6"),
        make_para(flow_index=10, text="附录\t7"),
        make_para(flow_index=11, text="第一章  引言", outline_level=0),
        make_para(flow_index=12, text="正文段落"),
        make_para(flow_index=13, text="参考文献", outline_level=0),
        make_para(flow_index=14, text="[1] Turing A M. Computing machinery and intelligence[J]."),
    ])

    sections = detect_sections(doc)

    assert sections["table-of-contents"].start == 2
    assert sections["table-of-contents"].end == 11
    assert sections["main-text"].start == 11
    assert sections["main-text"].end == 13
    assert sections["references"].start == 13
    assert "body" not in sections


def test_detect_sections_uses_text_anchors_without_h1():
    doc = make_doc([
        make_para(flow_index=0, text="封面"),
        make_para(flow_index=1, text="摘  要", outline_level=None),
        make_para(flow_index=2, text="中文摘要正文"),
        make_para(flow_index=3, text="ABSTRACT", outline_level=None),
        make_para(flow_index=4, text="English abstract"),
        make_para(flow_index=5, text="目    录", outline_level=None),
        make_para(flow_index=6, text="", runs=[]),
        make_para(flow_index=7, text="第一章  引言\t1"),
        make_para(flow_index=8, text="第一章  引言", outline_level=None),
        make_para(flow_index=9, text="正文"),
        make_para(flow_index=10, text="参考文献", outline_level=None),
        make_para(flow_index=11, text="文献条目"),
        make_para(flow_index=12, text="致    谢", outline_level=None),
        make_para(flow_index=13, text="感谢内容"),
        make_para(flow_index=14, text="附    录", outline_level=None),
    ])

    sections = detect_sections(doc)

    assert sections["abstract"].start == 1
    assert sections["abstract"].end == 5
    assert sections["abstract-chinese"].start == 1
    assert sections["abstract-chinese"].end == 3
    assert sections["abstract-english"].start == 3
    assert sections["abstract-english"].end == 5
    assert sections["table-of-contents"].start == 5
    assert sections["main-text"].start == 8
    assert sections["references"].start == 10
    assert sections["acknowledgements"].start == 12
    assert sections["appendix"].start == 14
    assert "abstract_cn" not in sections
    assert "abstract_en" not in sections
    assert "body" not in sections
    assert "thanks" not in sections


def test_detect_sections_uses_heading_level_one_style_as_main_text_start():
    doc = make_doc([
        make_para(flow_index=0, text="摘    要"),
        make_para(flow_index=1, text="摘要正文"),
        make_para(flow_index=2, text="目    录"),
        make_para(flow_index=3, text="", runs=[]),
        make_para(flow_index=4, text="随便", outline_level=0),
        make_para(flow_index=5, text="正文"),
        make_para(flow_index=6, text="参考文献", outline_level=0),
    ])

    sections = detect_sections(doc)

    assert sections["main-text"].start == 4
    assert sections["main-text"].end == 6


def test_detect_english_abstract_anchor_is_case_insensitive_for_rule_checks():
    doc = make_doc([
        make_para(flow_index=0, text="摘    要"),
        make_para(flow_index=1, text="中文摘要正文"),
        make_para(flow_index=2, text="ABSTRAcT"),
        make_para(flow_index=3, text="English abstract"),
        make_para(flow_index=4, text="目    录"),
    ])

    sections = detect_sections(doc)

    assert sections["abstract-chinese"].start == 0
    assert sections["abstract-chinese"].end == 2
    assert sections["abstract-english"].start == 2
    assert sections["abstract-english"].end == 4


def test_paragraphs_in_range_returns_only_paragraph_blocks():
    doc = make_doc([
        make_para(flow_index=0, text="目    录"),
        make_para(flow_index=1, text="", runs=[]),
        make_para(flow_index=2, text="第一章  引言\t1"),
        make_para(flow_index=3, text="第一章  引言", outline_level=0),
    ])
    toc = detect_sections(doc)["table-of-contents"]

    assert [p.text for p in paragraphs_in_range(doc, toc)] == [
        "目    录",
        "",
        "第一章  引言\t1",
    ]
