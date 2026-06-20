from pathlib import Path

from thesis_review.rules.acknowledgements_rules import (
    AcknowledgementsBodyChecker,
    AcknowledgementsTitleChecker,
)
from thesis_review.rules.context import build_rule_context
from tests.support.model_builders import make_doc, make_para, make_run


def context_for(doc):
    return build_rule_context(
        doc,
        rules_root=Path(__file__).resolve().parents[3] / "docs" / "rules",
    )


def run(text, east="宋体", latin="Times New Roman", size=12.0, bold=False):
    return make_run(
        text=text,
        font_east_asian=east,
        font_latin=latin,
        size_pt=size,
        bold=bold,
    )


def doc_with_ack(*ack_paras):
    return make_doc([
        make_para(flow_index=0, text="第一章  引言"),
        make_para(flow_index=1, text="参考文献"),
        make_para(flow_index=2, text="[1] 文献"),
        *ack_paras,
        make_para(flow_index=2 + len(ack_paras) + 1, text="附    录"),
    ])


def title(flow_index=3, text="致    谢", east="黑体", size=16.0, alignment="center"):
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment=alignment,
        first_line_indent_chars=0.0,
        runs=[run(text, east=east, latin="Times New Roman", size=size)],
    )


def body(
    flow_index=5,
    east="宋体",
    latin="Times New Roman",
    size=12.0,
    line_spacing=1.5,
    indent=2.0,
    alignment="justify",
):
    text = "感谢老师和 classmates 2026。"
    return make_para(
        flow_index=flow_index,
        text=text,
        alignment=alignment,
        line_spacing=line_spacing,
        first_line_indent_chars=indent,
        runs=[
            run("感谢老师和 ", east=east, latin=latin, size=size),
            run("classmates 2026", east=east, latin=latin, size=size),
            run("。", east=east, latin=latin, size=size),
        ],
    )


def empty(flow_index):
    return make_para(flow_index=flow_index, text="", runs=[])


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def test_acknowledgements_title_checker_accepts_valid_title():
    doc = doc_with_ack(title(3), empty(4), body(5))

    assert AcknowledgementsTitleChecker().check(context_for(doc)) == []


def test_acknowledgements_title_checker_flags_case_rules():
    doc = doc_with_ack(
        title(3, text="致谢", east="宋体", size=12.0, alignment="left"),
        body(4),
    )

    issues = AcknowledgementsTitleChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "acknowledgements-title-001",
        "acknowledgements-title-002",
        "acknowledgements-title-003",
        "acknowledgements-title-004",
        "acknowledgements-title-005",
    }


def test_acknowledgements_body_checker_accepts_valid_body():
    doc = doc_with_ack(title(3), empty(4), body(5))

    assert AcknowledgementsBodyChecker().check(context_for(doc)) == []


def test_acknowledgements_body_checker_flags_case_rules():
    doc = doc_with_ack(
        title(3),
        empty(4),
        body(
            5,
            east="仿宋",
            latin="Arial",
            size=10.5,
            line_spacing=1.0,
            indent=0.0,
            alignment="left",
        ),
    )

    issues = AcknowledgementsBodyChecker().check(context_for(doc))

    assert rule_ids(issues) == {
        "acknowledgements-body-001",
        "acknowledgements-body-002",
        "acknowledgements-body-003",
        "acknowledgements-body-004",
        "acknowledgements-body-005",
        "acknowledgements-body-006",
    }
