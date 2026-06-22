from pathlib import Path

from thesis_review.rules.context import build_rule_context
from thesis_review.rules.main_text_rules import (
    MainTextFigureCaptionChecker,
    MainTextFormulaChecker,
    MainTextHeadingChecker,
    MainTextParagraphChecker,
    MainTextReferenceCitationChecker,
    MainTextTableCaptionChecker,
)
from tests.support.model_builders import (
    make_doc,
    make_image,
    make_para,
    make_run,
    make_table,
    make_tab_stop,
)


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
    }
    assert "main-text-heading-level-one-006" not in rule_ids(issues)


def test_main_text_heading_checker_ignores_deprecated_new_page_rule():
    doc = thesis_doc(
        h1(5, page_break_before=False),
        body(6),
    )

    issues = MainTextHeadingChecker().check(context_for(doc))

    assert "main-text-heading-level-one-006" not in rule_ids(issues)


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


def paragraph(
    flow_index=9,
    east="宋体",
    latin="Times New Roman",
    size=12.0,
    line_spacing=1.5,
    indent=2.0,
    alignment="justify",
):
    text = "线性表是最常用的数据结构 Data 2026。"
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment=alignment,
        line_spacing=line_spacing,
        first_line_indent_chars=indent,
        runs=[
            run("线性表是最常用的数据结构 ", east=east, latin=latin, size=size),
            run("Data 2026", east=east, latin=latin, size=size),
            run("。", east=east, latin=latin, size=size),
        ],
    )


def test_main_text_paragraph_checker_accepts_valid_paragraph():
    doc = thesis_doc(h1(5), empty(6), paragraph(7))

    assert MainTextParagraphChecker().check(context_for(doc)) == []


def test_main_text_paragraph_checker_flags_case_rules():
    doc = thesis_doc(
        h1(5),
        empty(6),
        paragraph(
            7,
            east="仿宋",
            latin="Arial",
            size=10.5,
            line_spacing=1.0,
            indent=0.0,
            alignment="left",
        ),
    )

    issues = MainTextParagraphChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "main-text-paragraph-001",
        "main-text-paragraph-002",
        "main-text-paragraph-003",
        "main-text-paragraph-004",
        "main-text-paragraph-005",
        "main-text-paragraph-006",
    }


def test_main_text_paragraph_checker_skips_captions_and_formula_like_paragraphs():
    doc = thesis_doc(
        h1(5),
        empty(6),
        make_para(
            flow_index=7,
            text="图3-1 过阻尼响应",
            alignment="center",
            runs=[run("图3-1 过阻尼响应", east="仿宋", size=10.5)],
        ),
        make_para(
            flow_index=8,
            text="表4-1 实验数据",
            alignment="center",
            runs=[run("表4-1 实验数据", east="仿宋", size=10.5)],
        ),
        make_para(
            flow_index=9,
            text="(3-1)",
            alignment="right",
            runs=[run("(3-1)", east="仿宋", size=10.5)],
        ),
    )

    assert MainTextParagraphChecker().check(context_for(doc)) == []


def test_main_text_paragraph_checker_skips_placeholders_and_continued_tables():
    doc = thesis_doc(
        h1(5),
        empty(6),
        make_para(
            flow_index=7,
            text="……",
            alignment="left",
            runs=[run("……", east="宋体", latin="宋体", size=12.0)],
        ),
        make_para(
            flow_index=8,
            text="续表4-1",
            alignment="right",
            runs=[run("续表4-1", east="宋体", latin="Times New Roman", size=10.5)],
        ),
    )

    assert MainTextParagraphChecker().check(context_for(doc)) == []


def citation_para(
    flow_index=7,
    token="[1]",
    superscript=True,
    latin="Times New Roman",
    size=12.0,
):
    return make_para(
        flow_index=flow_index,
        text=f"线性表{token}是常用结构。",
        alignment="justify",
        line_spacing=1.5,
        first_line_indent_chars=2.0,
        runs=[
            run("线性表"),
            run(token, latin=latin, size=size, superscript=superscript),
            run("是常用结构。"),
        ],
    )


def test_main_text_reference_citation_checker_accepts_valid_citation():
    doc = thesis_doc(h1(5), empty(6), citation_para(7))

    assert MainTextReferenceCitationChecker().check(context_for(doc)) == []


def test_main_text_reference_citation_checker_flags_case_rules():
    doc = thesis_doc(
        h1(5),
        empty(6),
        citation_para(7, token="[a1]", superscript=False, latin="Arial", size=14.0),
    )

    issues = MainTextReferenceCitationChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "main-text-reference-citation-001",
        "main-text-reference-citation-002",
        "main-text-reference-citation-003",
        "main-text-reference-citation-004",
    }


def formula_para(
    flow_index=7,
    text="a = b + c\t(1-1)",
    alignment="center",
    latin="Times New Roman",
    size=10.5,
    tab_stops=None,
):
    if tab_stops is None:
        tab_stops = [
            make_tab_stop(position_mm=75.0, alignment="center"),
            make_tab_stop(position_mm=150.0, alignment="right"),
        ]
    return make_para(
        flow_index=flow_index,
        text=text,
        style_name="公式",
        alignment=alignment,
        first_line_indent_chars=0.0,
        contains_math=True,
        math_object_count=1,
        tab_stops=tab_stops,
        runs=[
            run("a = b + c\t", latin=latin, size=12.0),
            run("(1-1)", latin=latin, size=size),
        ],
    )


def test_main_text_formula_checker_accepts_valid_formula():
    doc = thesis_doc(h1(5, text="第一章  引言"), empty(6), formula_para(7))

    assert MainTextFormulaChecker().check(context_for(doc)) == []


def test_main_text_formula_checker_flags_numbering_font_and_size():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        formula_para(
            7,
            text="a = b + c\t(1-2)",
            alignment="left",
            latin="Arial",
            size=12.0,
            tab_stops=[],
        ),
    )

    issues = MainTextFormulaChecker().check(context_for(doc))

    assert rule_ids(issues) >= {
        "main-text-formula-002",
        "main-text-formula-005",
        "main-text-formula-006",
    }
    assert "main-text-formula-003" not in rule_ids(issues)
    assert "main-text-formula-004" not in rule_ids(issues)


def test_main_text_formula_checker_flags_missing_formula_number_only_for_number_rules():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        formula_para(7, text="a = b + c", tab_stops=[]),
    )

    issues = MainTextFormulaChecker().check(context_for(doc))

    assert "main-text-formula-001" in rule_ids(issues)


def test_main_text_formula_checker_pairs_blank_math_paragraph_with_number_paragraph():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        make_para(
            flow_index=7,
            text="       ",
            alignment="center",
            first_line_indent_chars=0.0,
            contains_math=True,
            math_object_count=1,
            runs=[],
        ),
        make_para(
            flow_index=8,
            text="       (1-1)",
            alignment="right",
            first_line_indent_chars=0.0,
            contains_math=True,
            math_object_count=1,
            runs=[run("       (1-1)", latin="Times New Roman", size=10.5)],
        ),
    )

    assert MainTextFormulaChecker().check(context_for(doc)) == []


def test_main_text_formula_checker_deduplicates_adjacent_blank_math_paragraphs():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        make_para(
            flow_index=7,
            text="       ",
            alignment="center",
            first_line_indent_chars=0.0,
            contains_math=True,
            math_object_count=1,
            runs=[],
        ),
        make_para(
            flow_index=8,
            text="",
            alignment="center",
            first_line_indent_chars=0.0,
            contains_math=True,
            math_object_count=1,
            runs=[],
        ),
    )

    issues = MainTextFormulaChecker().check(context_for(doc))

    assert rule_ids(issues) == {"main-text-formula-001"}


def figure_caption(
    flow_index=8,
    text="图1-1 过阻尼响应",
    east="宋体",
    size=10.5,
    alignment="center",
):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment=alignment,
        first_line_indent_chars=0.0,
        runs=[run(text, east=east, latin="Times New Roman", size=size)],
    )


def test_main_text_figure_caption_checker_accepts_valid_caption_below_image():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        make_image(flow_index=7),
        figure_caption(8),
    )

    assert MainTextFigureCaptionChecker().check(context_for(doc)) == []


def test_main_text_figure_caption_checker_ignores_deprecated_missing_caption_rule():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        make_image(flow_index=7),
        paragraph(8),
    )

    issues = MainTextFigureCaptionChecker().check(context_for(doc))

    assert "main-text-figure-caption-001" not in rule_ids(issues)


def test_main_text_figure_caption_checker_ignores_deprecated_position_rule():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        figure_caption(7),
        paragraph(8),
    )

    issues = MainTextFigureCaptionChecker().check(context_for(doc))

    assert "main-text-figure-caption-002" not in rule_ids(issues)


def test_main_text_figure_caption_checker_flags_caption_format_rules():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        make_image(flow_index=7),
        figure_caption(
            8,
            text="图1-2 过阻尼响应",
            east="仿宋",
            size=12.0,
            alignment="left",
        ),
    )

    issues = MainTextFigureCaptionChecker().check(context_for(doc))

    assert rule_ids(issues) >= {
        "main-text-figure-caption-003",
        "main-text-figure-caption-005",
        "main-text-figure-caption-006",
        "main-text-figure-caption-007",
    }


def table_caption(
    flow_index=7,
    text="表1-1 实验数据",
    east="宋体",
    size=10.5,
    alignment="center",
):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment=alignment,
        first_line_indent_chars=0.0,
        runs=[run(text, east=east, latin="Times New Roman", size=size)],
    )


def test_main_text_table_caption_checker_accepts_valid_caption_above_table():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        table_caption(7),
        make_table(flow_index=8),
    )

    assert MainTextTableCaptionChecker().check(context_for(doc)) == []


def test_main_text_table_caption_checker_ignores_deprecated_missing_caption_rule():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        make_table(flow_index=7),
    )

    issues = MainTextTableCaptionChecker().check(context_for(doc))

    assert "main-text-table-caption-001" not in rule_ids(issues)


def test_main_text_table_caption_checker_ignores_deprecated_position_rule():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        paragraph(7),
        table_caption(8),
    )

    issues = MainTextTableCaptionChecker().check(context_for(doc))

    assert "main-text-table-caption-002" not in rule_ids(issues)


def test_main_text_table_caption_checker_flags_caption_format_rules():
    doc = thesis_doc(
        h1(5, text="第一章  引言"),
        empty(6),
        table_caption(
            7,
            text="表1-2 实验数据",
            east="仿宋",
            size=12.0,
            alignment="left",
        ),
        make_table(flow_index=8),
    )

    issues = MainTextTableCaptionChecker().check(context_for(doc))

    assert rule_ids(issues) >= {
        "main-text-table-caption-003",
        "main-text-table-caption-005",
        "main-text-table-caption-006",
        "main-text-table-caption-007",
    }


def test_main_text_paragraph_checker_skips_math_object_paragraph():
    doc = thesis_doc(
        h1(5),
        empty(6),
        formula_para(7, text="a = b + c\t(1-1)", alignment="center"),
    )

    assert MainTextParagraphChecker().check(context_for(doc)) == []
