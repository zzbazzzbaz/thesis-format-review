"""只读 OOXML 结构辅助抽取。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

_NS = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "o": "urn:schemas-microsoft-com:office:office",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


@dataclass(frozen=True)
class ParagraphObjectInfo:
    text: str
    has_formula_object: bool


@dataclass(frozen=True)
class PageNumberFormatInfo:
    text: str
    font_east_asian: str | None = None
    font_latin: str | None = None
    size_pt: float | None = None


def _has_formula_object(paragraph: ET.Element) -> bool:
    return any(
        paragraph.findall(pattern, _NS)
        for pattern in (
            ".//m:oMath",
            ".//m:oMathPara",
            ".//w:object",
            ".//o:OLEObject",
        )
    )


def _paragraph_text(paragraph: ET.Element) -> str:
    return "".join(
        text.text or ""
        for text in paragraph.findall(".//w:t", _NS)
    )


def paragraph_object_infos(path: str | Path) -> list[ParagraphObjectInfo]:
    """返回 word/document.xml 中每个正文段落的文本和数学/OLE 对象标记。"""
    try:
        with ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml")
    except (BadZipFile, FileNotFoundError, KeyError, OSError):
        return []

    root = ET.fromstring(document_xml)
    body = root.find("w:body", _NS)
    if body is None:
        return []
    return [
        ParagraphObjectInfo(
            text=_paragraph_text(paragraph),
            has_formula_object=_has_formula_object(paragraph),
        )
        for paragraph in body.findall("w:p", _NS)
    ]


def paragraph_object_flags(path: str | Path) -> list[bool]:
    """返回 word/document.xml 中每个正文段落是否包含数学/OLE 对象。"""
    return [info.has_formula_object for info in paragraph_object_infos(path)]


def match_paragraph_object_flags(
    paragraph_texts: list[str],
    infos: list[ParagraphObjectInfo],
) -> list[bool]:
    """按段落文本顺序把 OOXML 对象标记对齐到 UNO 段落序列。"""
    flags: list[bool] = []
    search_from = 0
    for text in paragraph_texts:
        matched_index: int | None = None
        for index in range(search_from, len(infos)):
            if infos[index].text == text:
                matched_index = index
                break
        if matched_index is None:
            flags.append(False)
            continue
        flags.append(infos[matched_index].has_formula_object)
        search_from = matched_index + 1
    return flags


def _safe_xml_from_zip(archive: ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(archive.read(name))
    except (ET.ParseError, KeyError):
        return None


def _relationship_targets(archive: ZipFile) -> dict[str, str]:
    root = _safe_xml_from_zip(archive, "word/_rels/document.xml.rels")
    if root is None:
        return {}
    targets: dict[str, str] = {}
    for rel in root.findall("rel:Relationship", _NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            targets[rel_id] = target
    return targets


def _footer_targets(archive: ZipFile) -> list[str]:
    document = _safe_xml_from_zip(archive, "word/document.xml")
    if document is None:
        return []
    targets_by_id = _relationship_targets(archive)
    out: list[str] = []
    seen: set[str] = set()
    for reference in document.findall(".//w:footerReference", _NS):
        rel_id = reference.attrib.get(f"{{{_NS['r']}}}id")
        target = targets_by_id.get(rel_id or "")
        if not target:
            continue
        path = target if target.startswith("word/") else f"word/{target}"
        if path not in seen:
            out.append(path)
            seen.add(path)
    return out


def _half_points_to_points(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return int(value) / 2.0
    except ValueError:
        return None


def _run_font(run: ET.Element, *attrs: str) -> str | None:
    fonts = run.find("w:rPr/w:rFonts", _NS)
    if fonts is None:
        return None
    for attr in attrs:
        value = fonts.attrib.get(f"{{{_NS['w']}}}{attr}")
        if value:
            return value
    return None


def _run_size(run: ET.Element) -> float | None:
    size = run.find("w:rPr/w:sz", _NS)
    if size is None:
        return None
    return _half_points_to_points(size.attrib.get(f"{{{_NS['w']}}}val"))


def _page_field_result_run(paragraph: ET.Element) -> ET.Element | None:
    in_page_field = False
    after_separator = False
    for run in paragraph.findall("w:r", _NS):
        instr_text = "".join(
            node.text or ""
            for node in run.findall("w:instrText", _NS)
        )
        if "PAGE" in instr_text.upper():
            in_page_field = True
        fld_char = run.find("w:fldChar", _NS)
        if fld_char is not None:
            field_type = fld_char.attrib.get(f"{{{_NS['w']}}}fldCharType")
            if field_type == "begin":
                after_separator = False
            elif field_type == "separate" and in_page_field:
                after_separator = True
            elif field_type == "end" and in_page_field:
                in_page_field = False
                after_separator = False
            continue
        if in_page_field and after_separator and _paragraph_text(run).strip():
            return run
    return None


def footer_page_number_format(path: str | Path) -> PageNumberFormatInfo | None:
    """读取 docx 默认页脚 PAGE 字段显示 run 的字体和字号。"""
    try:
        with ZipFile(path) as archive:
            footer_targets = _footer_targets(archive)
            for target in footer_targets:
                footer = _safe_xml_from_zip(archive, target)
                if footer is None:
                    continue
                for paragraph in footer.findall("w:p", _NS):
                    run = _page_field_result_run(paragraph)
                    if run is None:
                        continue
                    return PageNumberFormatInfo(
                        text=_paragraph_text(run).strip(),
                        font_east_asian=_run_font(run, "eastAsia"),
                        font_latin=_run_font(run, "ascii", "hAnsi"),
                        size_pt=_run_size(run),
                    )
    except (BadZipFile, FileNotFoundError, OSError):
        return None
    return None
