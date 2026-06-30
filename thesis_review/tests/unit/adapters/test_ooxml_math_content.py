from __future__ import annotations

from zipfile import ZipFile
from xml.etree import ElementTree as ET

from thesis_review.adapters.ooxml.math_content import restore_math_content

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _docx(path, document_xml: str) -> None:
    with ZipFile(path, "w") as docx:
        docx.writestr("[Content_Types].xml", "<Types/>")
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/_rels/document.xml.rels", "<Relationships/>")


def _document(paragraphs: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:m="{M_NS}">
  <w:body>{paragraphs}</w:body>
</w:document>"""


def _p(text: str = "") -> str:
    if not text:
        return "<w:p/>"
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def _math_p(text: str = "") -> str:
    text_run = f"<w:r><w:t>{text}</w:t></w:r>" if text else ""
    return (
        f"<w:p>{text_run}"
        "<m:oMathPara><m:oMath><m:r><m:t>x+y</m:t></m:r></m:oMath></m:oMathPara>"
        "</w:p>"
    )


def _paragraphs(path):
    with ZipFile(path) as docx:
        root = ET.fromstring(docx.read("word/document.xml"))
    return list(root.findall(f".//{{{W_NS}}}body/{{{W_NS}}}p"))


def _text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(f".//{{{W_NS}}}t"))


def _math_count(path) -> int:
    return sum(
        len(paragraph.findall(f".//{{{M_NS}}}oMath"))
        for paragraph in _paragraphs(path)
    )


def test_restore_math_content_restores_formula_only_and_inline_paragraphs(tmp_path):
    source = tmp_path / "source.docx"
    target = tmp_path / "target.docx"
    _docx(
        source,
        _document(
            _p("Before")
            + _p()
            + _math_p()
            + _p("Inline ")
            + _math_p("Formula text")
            + _p("After")
        ),
    )
    _docx(
        target,
        _document(
            _p("Before")
            + _p()
            + _p()
            + _p("Inline ")
            + _p("Formula text")
            + _p("After")
        ),
    )

    restore_math_content(source, target)

    paragraphs = _paragraphs(target)
    assert _math_count(target) == 2
    assert _text(paragraphs[1]) == ""
    assert len(paragraphs[1].findall(f".//{{{M_NS}}}oMath")) == 0
    assert len(paragraphs[2].findall(f".//{{{M_NS}}}oMath")) == 1
    assert _text(paragraphs[4]) == "Formula text"
    assert len(paragraphs[4].findall(f".//{{{M_NS}}}oMath")) == 1


def test_restore_math_content_preserves_non_document_parts(tmp_path):
    source = tmp_path / "source.docx"
    target = tmp_path / "target.docx"
    _docx(source, _document(_math_p()))
    _docx(target, _document(_p()))

    restore_math_content(source, target)

    with ZipFile(target) as docx:
        assert docx.read("word/_rels/document.xml.rels") == b"<Relationships/>"
