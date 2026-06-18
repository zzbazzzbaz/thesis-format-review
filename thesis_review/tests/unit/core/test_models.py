import pytest
from pydantic import ValidationError

from thesis_review.core.models import (
    DocumentModel,
    ImageBlock,
    Issue,
    Location,
    ParagraphBlock,
    RunSpan,
    TableBlock,
)


def test_runspan_holds_char_level_fields():
    run = RunSpan(
        id="b-0001-r-0001",
        text="本文",
        run_index=0,
        font_east_asian="宋体",
        font_latin=None,
        size_pt=12.0,
        bold=False,
        italic=False,
    )
    assert run.font_east_asian == "宋体"
    assert run.size_pt == 12.0


def test_paragraph_holds_para_level_fields_and_runs():
    para = ParagraphBlock(
        id="b-0001",
        flow_index=1,
        type_index=0,
        text="本文",
        style_name="正文",
        outline_level=None,
        alignment="left",
        line_spacing=1.5,
        first_line_indent_chars=2.0,
        runs=[
            RunSpan(
                id="b-0001-r-0001",
                text="本文",
                run_index=0,
                font_east_asian="宋体",
                font_latin=None,
                size_pt=12.0,
                bold=False,
                italic=False,
            )
        ],
    )
    assert para.outline_level is None
    assert len(para.runs) == 1


def test_document_holds_ordered_blocks():
    doc = DocumentModel(source_docx="in.docx", blocks=[])
    assert doc.source_docx == "in.docx"
    assert doc.blocks == []


def test_document_block_discriminated_union_parses_table_and_image():
    doc = DocumentModel(
        source_docx="in.docx",
        blocks=[
            {
                "id": "b-0000",
                "kind": "table",
                "flow_index": 0,
                "type_index": 0,
                "row_count": 2,
                "column_count": 3,
                "text": "表格内容",
            },
            {
                "id": "b-0001",
                "kind": "image",
                "flow_index": 1,
                "type_index": 0,
                "name": "Picture 1",
                "alt_text": "示意图",
                "width_mm": 50.0,
                "height_mm": 30.0,
            },
        ],
    )
    assert isinstance(doc.blocks[0], TableBlock)
    assert isinstance(doc.blocks[1], ImageBlock)
    assert doc.blocks[0].type_index == 0
    assert doc.blocks[1].flow_index == 1


def test_issue_with_location():
    issue = Issue(
        rule_id="table-of-contents-entry-004",
        category="structure",
        severity="error",
        message="目录条目中文字体应为宋体",
        expected="宋体",
        actual="楷体",
        location=Location(
            target="run",
            block_id="b-0001",
            block_kind="paragraph",
            flow_index=1,
            run_id="b-0001-r-0001",
            run_index=0,
        ),
    )
    assert issue.location.target == "run"
    assert issue.actual == "楷体"


def test_location_block_target_allows_no_run_fields():
    loc = Location(
        target="block",
        block_id="b-0001",
        block_kind="paragraph",
        flow_index=1,
    )
    assert loc.run_id is None
    assert loc.run_index is None


def test_run_location_requires_run_fields():
    with pytest.raises(ValidationError):
        Location(
            target="run",
            block_id="b-0001",
            block_kind="paragraph",
            flow_index=1,
        )


def test_block_location_rejects_run_fields():
    with pytest.raises(ValidationError):
        Location(
            target="block",
            block_id="b-0001",
            block_kind="paragraph",
            flow_index=1,
            run_id="b-0001-r-0000",
            run_index=0,
        )


def test_run_location_rejects_non_paragraph_block():
    with pytest.raises(ValidationError):
        Location(
            target="run",
            block_id="b-0001",
            block_kind="table",
            flow_index=1,
            run_id="b-0001-r-0000",
            run_index=0,
        )


def test_issue_rejects_unknown_severity():
    with pytest.raises(ValidationError):
        Issue(
            rule_id="table-of-contents-title-001",
            category="structure",
            severity="fatal",
            message="bad severity",
            location=Location(
                target="block",
                block_id="b-0001",
                block_kind="paragraph",
                flow_index=1,
            ),
        )
