from thesis_review.models import (
    DocumentModel,
    Issue,
    Location,
    ParagraphBlock,
    RunSpan,
)


def test_runspan_holds_char_level_fields():
    run = RunSpan(
        id="p-0001-r-0001",
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
        id="p-0001",
        text="本文",
        paragraph_index=0,
        style_name="正文",
        outline_level=None,
        alignment="left",
        line_spacing=1.5,
        first_line_indent_chars=2.0,
        runs=[
            RunSpan(
                id="p-0001-r-0001",
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


def test_document_holds_paragraphs():
    doc = DocumentModel(source_docx="in.docx", paragraphs=[])
    assert doc.source_docx == "in.docx"
    assert doc.paragraphs == []


def test_issue_with_location():
    issue = Issue(
        rule_id="format.body.font",
        category="format",
        severity="error",
        message="正文中文字体应为宋体",
        expected="宋体",
        actual="楷体",
        location=Location(
            kind="run",
            block_id="p-0001",
            paragraph_index=0,
            run_id="p-0001-r-0001",
            run_index=0,
        ),
    )
    assert issue.location.kind == "run"
    assert issue.actual == "楷体"


def test_location_paragraph_kind_allows_optional_run_fields():
    loc = Location(kind="paragraph", block_id="p-0001", paragraph_index=3)
    assert loc.run_id is None
    assert loc.run_index is None
