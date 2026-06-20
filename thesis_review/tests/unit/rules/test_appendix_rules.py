from pathlib import Path

from thesis_review.rules.appendix_rules import AppendixBodyChecker, AppendixTitleChecker
from thesis_review.rules.context import build_rule_context
from tests.support.model_builders import make_doc, make_para, make_run


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def run(text, east="宋体", latin="Times New Roman", size=12.0):
    return make_run(text=text, font_east_asian=east, font_latin=latin, size_pt=size)


def doc_with_appendix(*appendix_paras):
    return make_doc([
        make_para(flow_index=0, text="第一章  引言"),
        make_para(flow_index=1, text="参考文献"),
        make_para(flow_index=2, text="[1] 文献"),
        make_para(flow_index=3, text="致    谢"),
        make_para(flow_index=4, text="感谢内容"),
        *appendix_paras,
    ])


def title(flow_index=5, text="附    录", east="黑体", size=16.0, alignment="center"):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment=alignment,
        first_line_indent_chars=0.0,
        runs=[run(text, east=east, latin="Times New Roman", size=size)],
    )


def body(
    flow_index=7,
    east="宋体",
    latin="Times New Roman",
    size=12.0,
    line_spacing=1.5,
    indent=2.0,
    alignment="justify",
):
    text = "附录A名词术语及 abbreviation 2026。"
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment=alignment,
        line_spacing=line_spacing,
        first_line_indent_chars=indent,
        runs=[
            run("附录A名词术语及 ", east=east, latin=latin, size=size),
            run("abbreviation 2026", east=east, latin=latin, size=size),
            run("。", east=east, latin=latin, size=size),
        ],
    )


def empty(flow_index):
    return make_para(flow_index=flow_index, text="", runs=[])


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def test_appendix_title_checker_flags_case_rules():
    doc = doc_with_appendix(
        title(5, text="附录", east="宋体", size=12.0, alignment="left"),
        body(6),
    )

    issues = AppendixTitleChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "appendix-title-001",
        "appendix-title-002",
        "appendix-title-003",
        "appendix-title-004",
        "appendix-title-005",
    }


def test_appendix_body_checker_flags_case_rules():
    doc = doc_with_appendix(
        title(5),
        empty(6),
        body(
            7,
            east="仿宋",
            latin="Arial",
            size=10.5,
            line_spacing=1.0,
            indent=0.0,
            alignment="left",
        ),
    )

    issues = AppendixBodyChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "appendix-body-001",
        "appendix-body-002",
        "appendix-body-003",
        "appendix-body-004",
        "appendix-body-005",
        "appendix-body-006",
    }
