from pathlib import Path

from thesis_review.rules.context import build_rule_context
from thesis_review.rules.global_rules import (
    GlobalFooterPageNumberChecker,
    GlobalHeaderChecker,
)
from tests.support.model_builders import (
    make_doc,
    make_formatted_run,
    make_header_footer_para,
    make_page_style,
    make_para,
)


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def thesis_doc(page_style, style_name="正文"):
    return make_doc(
        [
            make_para(flow_index=0, text="封面", page_style_name="封面"),
            make_para(flow_index=1, text="摘    要", page_style_name=style_name),
            make_para(flow_index=2, text="摘要正文", page_style_name=style_name),
            make_para(flow_index=3, text="目    录", page_style_name=style_name),
            make_para(flow_index=4, text="第一章  引言", page_style_name=style_name),
            make_para(flow_index=5, text="参考文献", page_style_name=style_name),
        ],
        page_styles=[page_style],
    )


def valid_header():
    return make_header_footer_para(
        text="山东石油化工学院本科毕业设计（论文）",
        alignment="center",
        runs=[
            make_formatted_run(
                text="山东石油化工学院本科毕业设计（论文）",
                font_east_asian="黑体",
                font_latin="Times New Roman",
                size_pt=10.5,
            )
        ],
    )


def valid_footer():
    return make_header_footer_para(
        text="1",
        alignment="center",
        runs=[
            make_formatted_run(
                text="1",
                font_east_asian=None,
                font_latin="Times New Roman",
                size_pt=10.5,
            )
        ],
        has_page_number_field=True,
        page_number_text="1",
        page_number_format="arabic",
    )


def test_global_header_checker_accepts_valid_header():
    style = make_page_style(name="正文", header_paragraphs=[valid_header()])
    doc = thesis_doc(style)

    assert GlobalHeaderChecker().check(context_for(doc)) == []


def test_global_header_checker_flags_text_font_size_and_alignment():
    style = make_page_style(
        name="正文",
        header_paragraphs=[
            make_header_footer_para(
                text="错误页眉",
                alignment="left",
                runs=[
                    make_formatted_run(
                        text="错误页眉",
                        font_east_asian="宋体",
                        size_pt=12.0,
                    )
                ],
            )
        ],
    )
    doc = thesis_doc(style)

    issues = GlobalHeaderChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "global-header-001",
        "global-header-002",
        "global-header-003",
        "global-header-004",
    }
    assert {issue.location.flow_index for issue in issues} == {1}


def test_global_header_checker_reports_missing_header_once():
    style = make_page_style(name="正文", header_paragraphs=[])
    doc = thesis_doc(style)

    issues = GlobalHeaderChecker().check(context_for(doc))

    assert [issue.rule_id for issue in issues] == ["global-header-001"]
    assert issues[0].actual == "未识别"


def test_global_footer_checker_accepts_valid_page_number():
    style = make_page_style(
        name="正文",
        header_paragraphs=[valid_header()],
        footer_paragraphs=[valid_footer()],
    )
    doc = thesis_doc(style)

    assert GlobalFooterPageNumberChecker().check(context_for(doc)) == []


def test_global_footer_checker_flags_page_number_format_alignment_font_and_size():
    style = make_page_style(
        name="正文",
        footer_paragraphs=[
            make_header_footer_para(
                text="IV",
                alignment="right",
                runs=[
                    make_formatted_run(
                        text="IV",
                        font_latin="Arial",
                        size_pt=12.0,
                    )
                ],
                has_page_number_field=True,
                page_number_text="IV",
                page_number_format="roman",
            )
        ],
    )
    doc = thesis_doc(style)

    issues = GlobalFooterPageNumberChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "global-footer-page-number-001",
        "global-footer-page-number-003",
        "global-footer-page-number-004",
        "global-footer-page-number-005",
    }


def test_global_footer_checker_reports_missing_page_number_once():
    style = make_page_style(name="正文", footer_paragraphs=[])
    doc = thesis_doc(style)

    issues = GlobalFooterPageNumberChecker().check(context_for(doc))

    assert [issue.rule_id for issue in issues] == ["global-footer-page-number-001"]
    assert issues[0].actual == "未识别页码"
