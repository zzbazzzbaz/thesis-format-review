"""OOXML 字体资产修复测试。"""
from __future__ import annotations

from zipfile import ZIP_DEFLATED, ZipFile

from thesis_review.adapters.ooxml.font_assets import restore_font_assets


def write_docx(path, parts: dict[str, bytes]) -> None:
    with ZipFile(path, "w", ZIP_DEFLATED) as docx:
        for name, data in parts.items():
            docx.writestr(name, data)


def read_part(path, name: str) -> bytes:
    with ZipFile(path) as docx:
        return docx.read(name)


def names(path) -> set[str]:
    with ZipFile(path) as docx:
        return set(docx.namelist())


def test_restore_font_assets_replaces_theme_font_table_and_embedded_fonts(tmp_path):
    source = tmp_path / "source.docx"
    target = tmp_path / "target.docx"
    write_docx(
        source,
        {
            "[Content_Types].xml": b"source content types",
            "word/document.xml": b"source document",
            "word/theme/theme1.xml": b"source theme",
            "word/fontTable.xml": b"source font table",
            "word/_rels/fontTable.xml.rels": b"source font rels",
            "word/fonts/font1.odttf": b"source font bytes",
        },
    )
    write_docx(
        target,
        {
            "[Content_Types].xml": b"target content types",
            "word/document.xml": b"target document",
            "word/theme/theme1.xml": b"target theme",
            "word/fontTable.xml": b"target font table",
            "word/fonts/stale.odttf": b"stale font bytes",
        },
    )

    restore_font_assets(source, target)

    assert read_part(target, "word/theme/theme1.xml") == b"source theme"
    assert read_part(target, "word/fontTable.xml") == b"source font table"
    assert read_part(target, "word/_rels/fontTable.xml.rels") == b"source font rels"
    assert read_part(target, "word/fonts/font1.odttf") == b"source font bytes"
    assert "word/fonts/stale.odttf" not in names(target)
    assert read_part(target, "word/document.xml") == b"target document"
    assert read_part(target, "[Content_Types].xml") == b"target content types"
