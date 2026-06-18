"""文档分区测试。"""
from __future__ import annotations

from thesis_review.sections import detect_sections
from thesis_review.sections import norm_text
from thesis_review.sections import paragraphs_in_range
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
        make_para(flow_index=4, text="第一章  引言\t1"),
        make_para(flow_index=5, text="2.1 线性表的定义\t2"),
        make_para(flow_index=6, text="第一章  引言", outline_level=0),
        make_para(flow_index=7, text="正文段落"),
        make_para(flow_index=8, text="参考文献", outline_level=0),
        make_para(flow_index=9, text="[1] Turing A M. Computing machinery and intelligence[J]."),
    ])

    sections = detect_sections(doc)

    assert sections["table-of-contents"].start == 2
    assert sections["table-of-contents"].end == 6
    assert sections["body"].start == 6
    assert sections["body"].end == 8
    assert sections["references"].start == 8


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

    assert sections["abstract_cn"].start == 1
    assert sections["abstract_en"].start == 3
    assert sections["table-of-contents"].start == 5
    assert sections["body"].start == 8
    assert sections["references"].start == 10
    assert sections["thanks"].start == 12
    assert sections["appendix"].start == 14


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
