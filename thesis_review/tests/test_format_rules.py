from thesis_review.rules.format_rules import BodyFontRule
from thesis_review.rules.format_rules import BodyFontSizeRule
from thesis_review.rules.format_rules import FirstLineIndentRule
from thesis_review.rules.format_rules import LineSpacingRule
from tests.builders import make_doc, make_para, make_run


def test_body_font_ok_when_songti():
    doc = make_doc([make_para(runs=[make_run(font_east_asian="宋体")])])
    assert doc.paragraphs[0].runs[0].id.startswith(doc.paragraphs[0].id)
    assert BodyFontRule().check(doc) == []


def test_body_font_flags_wrong_font():
    doc = make_doc([make_para(runs=[make_run(font_east_asian="楷体")])])
    issues = BodyFontRule().check(doc)
    assert len(issues) == 1
    assert issues[0].rule_id == "format.body.font"
    assert issues[0].expected == "宋体"
    assert issues[0].actual == "楷体"
    assert issues[0].location.kind == "run"


def test_body_font_skips_headings():
    doc = make_doc([
        make_para(outline_level=0, runs=[make_run(font_east_asian="黑体")])
    ])
    assert BodyFontRule().check(doc) == []


def test_body_size_ok_when_xiaosi():
    doc = make_doc([make_para(runs=[make_run(size_pt=12.0)])])
    assert BodyFontSizeRule().check(doc) == []


def test_body_size_flags_wrong_size():
    doc = make_doc([make_para(runs=[make_run(size_pt=14.0)])])
    issues = BodyFontSizeRule().check(doc)
    assert len(issues) == 1
    assert issues[0].rule_id == "format.body.size"
    assert issues[0].expected == "12.0"
    assert issues[0].actual == "14.0"


def test_body_size_skips_headings():
    doc = make_doc([make_para(outline_level=0, runs=[make_run(size_pt=22.0)])])
    assert BodyFontSizeRule().check(doc) == []


def test_line_spacing_ok_when_1_5():
    doc = make_doc([make_para(line_spacing=1.5)])
    assert LineSpacingRule().check(doc) == []


def test_line_spacing_flags_wrong_value():
    doc = make_doc([make_para(line_spacing=1.0)])
    issues = LineSpacingRule().check(doc)
    assert len(issues) == 1
    assert issues[0].rule_id == "format.body.line_spacing"
    assert issues[0].location.kind == "paragraph"


def test_line_spacing_skips_headings():
    doc = make_doc([make_para(outline_level=0, line_spacing=1.0)])
    assert LineSpacingRule().check(doc) == []


def test_line_spacing_ignores_none():
    doc = make_doc([make_para(line_spacing=None)])
    assert LineSpacingRule().check(doc) == []


def test_indent_ok_when_2_chars():
    doc = make_doc([make_para(first_line_indent_chars=2.0)])
    assert FirstLineIndentRule().check(doc) == []


def test_indent_flags_wrong_value():
    doc = make_doc([make_para(first_line_indent_chars=0.0)])
    issues = FirstLineIndentRule().check(doc)
    assert len(issues) == 1
    assert issues[0].rule_id == "format.body.indent"
    assert issues[0].location.kind == "paragraph"


def test_indent_skips_headings():
    doc = make_doc([make_para(outline_level=0, first_line_indent_chars=0.0)])
    assert FirstLineIndentRule().check(doc) == []


def test_indent_ignores_none():
    doc = make_doc([make_para(first_line_indent_chars=None)])
    assert FirstLineIndentRule().check(doc) == []
