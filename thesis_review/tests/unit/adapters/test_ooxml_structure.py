"""OOXML 结构辅助抽取测试。"""
from __future__ import annotations

from zipfile import ZipFile

from thesis_review.adapters.ooxml.structure import (
    ParagraphObjectInfo,
    footer_page_number_format,
    match_paragraph_object_flags,
    paragraph_object_flags,
)


def test_paragraph_object_flags_marks_math_and_ole_object_paragraphs(tmp_path):
    docx = tmp_path / "objects.docx"
    document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document
    xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
    xmlns:o="urn:schemas-microsoft-com:office:office">
  <w:body>
    <w:p><w:r><w:t>普通段落</w:t></w:r></w:p>
    <w:p><w:r><m:oMath /></w:r></w:p>
    <w:p><w:r><w:object><o:OLEObject /></w:object></w:r></w:p>
  </w:body>
</w:document>
"""
    with ZipFile(docx, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    assert paragraph_object_flags(docx) == [False, True, True]


def test_paragraph_object_flags_returns_empty_for_non_docx_path(tmp_path):
    assert paragraph_object_flags(tmp_path / "missing.docx") == []


def test_match_paragraph_object_flags_aligns_by_text_after_skipped_ooxml_paragraphs():
    infos = [
        ParagraphObjectInfo(text="封面图片", has_formula_object=False),
        ParagraphObjectInfo(text="       ", has_formula_object=True),
        ParagraphObjectInfo(text="", has_formula_object=True),
        ParagraphObjectInfo(text="正文段落", has_formula_object=False),
        ParagraphObjectInfo(text="       (3-2)", has_formula_object=True),
    ]

    assert match_paragraph_object_flags(["正文段落", "       (3-2)"], infos) == [
        False,
        True,
    ]


def test_footer_page_number_format_reads_field_result_run_size_and_font(tmp_path):
    docx = tmp_path / "footer.docx"
    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId5"
      Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
      Target="footer1.xml"/>
</Relationships>
"""
    document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr>
        <w:sectPr><w:footerReference w:type="default" r:id="rId5"/></w:sectPr>
      </w:pPr>
    </w:p>
  </w:body>
</w:document>
"""
    footer_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="separate"/></w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/>
        <w:sz w:val="21"/>
      </w:rPr>
      <w:t>7</w:t>
    </w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
</w:ftr>
"""
    with ZipFile(docx, "w") as archive:
        archive.writestr("word/_rels/document.xml.rels", rels_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/footer1.xml", footer_xml)

    page_number = footer_page_number_format(docx)

    assert page_number is not None
    assert page_number.text == "7"
    assert page_number.font_latin == "Times New Roman"
    assert page_number.size_pt == 10.5
