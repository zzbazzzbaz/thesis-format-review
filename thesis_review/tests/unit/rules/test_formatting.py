from pathlib import Path

from thesis_review.rules.context import build_rule_context
from thesis_review.rules.formatting import (
    block_location,
    contains_ascii,
    contains_chinese,
    display_alignment,
    display_indent,
    display_line_spacing,
    display_page_style_actual,
    display_size,
    empty_count_after,
    first_bad_run,
    has_indent,
    has_line_spacing,
    has_size,
    meaningful_runs,
    non_empty,
    run_location,
    runs_overlapping,
    section_blocks,
    section_paragraphs,
)
from tests.support.model_builders import make_doc, make_image, make_para, make_run, make_table


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def test_locations_use_block_and_run_ids():
    para = make_para(flow_index=3, text="正文", runs=[make_run(text="正文")])
    run = para.runs[0]

    assert block_location(para).model_dump() == {
        "target": "block",
        "block_id": "b-0003",
        "block_kind": "paragraph",
        "flow_index": 3,
        "run_id": None,
        "run_index": None,
    }
    assert run_location(para, run).run_id == "b-0003-r-0000"


def test_block_location_supports_non_paragraph_blocks():
    table = make_table(flow_index=4, type_index=0)
    image = make_image(flow_index=5, type_index=0)

    assert block_location(table).model_dump() == {
        "target": "block",
        "block_id": "b-0004",
        "block_kind": "table",
        "flow_index": 4,
        "run_id": None,
        "run_index": None,
    }
    assert block_location(image).block_kind == "image"


def test_display_helpers_return_stable_actual_values():
    assert display_size(12.0) == "12pt"
    assert display_size(None) == "未识别"
    assert display_line_spacing(1.5) == "1.5 倍"
    assert display_line_spacing(None) == "未识别"
    assert display_indent(2.0) == "2 字符"
    assert display_indent(None) == "未识别"
    assert display_alignment("center") == "居中"
    assert display_alignment("justify") == "两端对齐"
    assert display_alignment(None) == "未识别"
    assert display_page_style_actual(None) == "未识别"
    assert display_page_style_actual("正文") == "正文"


def test_format_predicates_treat_none_as_failure():
    para = make_para(line_spacing=None, first_line_indent_chars=None)
    run = make_run(size_pt=None)

    assert has_size(run, 12.0) is False
    assert has_line_spacing(para, 1.5) is False
    assert has_indent(para, 2.0) is False


def test_paragraph_filters_and_empty_count_after():
    paragraphs = [
        make_para(flow_index=0, text="标题"),
        make_para(flow_index=1, text="", runs=[]),
        make_para(flow_index=2, text="", runs=[]),
        make_para(flow_index=3, text="正文"),
    ]

    assert [p.text for p in non_empty(paragraphs)] == ["标题", "正文"]
    assert empty_count_after(paragraphs, paragraphs[0]) == 2


def test_meaningful_runs_and_first_bad_run():
    para = make_para(
        text="正文 A",
        runs=[
            make_run(text=" "),
            make_run(text="正文", font_east_asian="宋体"),
            make_run(text="A", font_latin="Arial"),
        ],
    )

    assert [run.text for run in meaningful_runs(para)] == ["正文", "A"]
    bad = first_bad_run(para, lambda run: run.font_latin == "Times New Roman")
    assert bad is not None
    assert bad.text == "正文"


def test_text_type_detection():
    assert contains_chinese("中文，。") is True
    assert contains_chinese("ABC123") is False
    assert contains_ascii("ABC123") is True
    assert contains_ascii("中文") is False


def test_section_paragraphs_returns_detected_range():
    doc = make_doc([
        make_para(flow_index=0, text="封面"),
        make_para(flow_index=1, text="摘    要"),
        make_para(flow_index=2, text="摘要正文"),
        make_para(flow_index=3, text="目    录"),
    ])

    paragraphs = section_paragraphs(context_for(doc), "abstract-chinese")

    assert [para.text for para in paragraphs] == ["摘    要", "摘要正文"]


def test_section_blocks_returns_all_block_kinds_in_range():
    doc = make_doc([
        make_para(flow_index=0, text="摘    要"),
        make_para(flow_index=1, text="摘要正文"),
        make_para(flow_index=2, text="目    录"),
        make_para(flow_index=3, text=""),
        make_para(flow_index=4, text="第一章  引言"),
        make_image(flow_index=5),
        make_para(flow_index=6, text="图1-1 示例"),
        make_para(flow_index=7, text="参考文献"),
    ])

    blocks = section_blocks(context_for(doc), "main-text")

    assert [block.kind for block in blocks] == ["paragraph", "image", "paragraph"]


def test_runs_overlapping_returns_visible_runs_for_text_range():
    para = make_para(
        flow_index=1,
        text="公式(3-1)",
        runs=[
            make_run(text="公式"),
            make_run(text="(3-1)", font_latin="Arial", size_pt=10.5),
        ],
    )

    assert [run.text for run in runs_overlapping(para, 2, 7)] == ["(3-1)"]
