"""保留输入 docx 的 Office Math 公式内容。"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

_DOCUMENT_XML = "word/document.xml"

ET.register_namespace("w", _W_NS)
ET.register_namespace("m", _M_NS)


def _paragraphs(root: ET.Element) -> list[ET.Element]:
    return list(root.findall(f".//{{{_W_NS}}}body/{{{_W_NS}}}p"))


def _paragraph_text(paragraph: ET.Element) -> str:
    return "".join(
        node.text or "" for node in paragraph.findall(f".//{{{_W_NS}}}t")
    )


def _has_math(paragraph: ET.Element) -> bool:
    return (
        paragraph.find(f".//{{{_M_NS}}}oMath") is not None
        or paragraph.find(f".//{{{_M_NS}}}oMathPara") is not None
    )


def _replace_element(elements: list[ET.Element], index: int, replacement: ET.Element) -> None:
    target = elements[index]
    target.clear()
    target.tag = replacement.tag
    target.attrib.update(replacement.attrib)
    target.text = replacement.text
    target.tail = replacement.tail
    target.extend(deepcopy(list(replacement)))


def _find_next_text_match(
    target_paragraphs: list[ET.Element],
    start: int,
    text: str,
) -> int | None:
    for index in range(start, len(target_paragraphs)):
        if _paragraph_text(target_paragraphs[index]) == text:
            return index
    return None


def _find_next_empty(
    target_paragraphs: list[ET.Element],
    start: int,
) -> int | None:
    for index in range(start, len(target_paragraphs)):
        if not _paragraph_text(target_paragraphs[index]).strip():
            return index
    return None


def _restore_math_document_xml(source_xml: bytes, target_xml: bytes) -> bytes:
    source_root = ET.fromstring(source_xml)
    target_root = ET.fromstring(target_xml)
    source_paragraphs = _paragraphs(source_root)
    target_paragraphs = _paragraphs(target_root)

    target_pos = 0
    for source_paragraph in source_paragraphs:
        source_text = _paragraph_text(source_paragraph)
        if _has_math(source_paragraph):
            if source_text.strip():
                target_index = _find_next_text_match(
                    target_paragraphs,
                    target_pos,
                    source_text,
                )
            else:
                target_index = _find_next_empty(target_paragraphs, target_pos)
            if target_index is None:
                continue
            _replace_element(target_paragraphs, target_index, source_paragraph)
            target_pos = target_index + 1
            continue

        if source_text.strip():
            target_index = _find_next_text_match(
                target_paragraphs,
                target_pos,
                source_text,
            )
            if target_index is not None:
                target_pos = target_index + 1
            continue

        if (
            target_pos < len(target_paragraphs)
            and not _paragraph_text(target_paragraphs[target_pos]).strip()
        ):
            target_pos += 1

    return ET.tostring(target_root, encoding="utf-8", xml_declaration=True)


def restore_math_content(source_docx: str | Path, target_docx: str | Path) -> None:
    """把 source_docx 中的 Office Math 段落恢复到 target_docx。

    LibreOffice/UNO 另存 docx 时可能会移除正文中的 ``m:oMath`` 节点，
    但通常会保留对应空段落或普通文字。这里只替换含公式的段落，
    避免像整体恢复 document.xml 那样覆盖批注和大部分标注内容。
    """
    source_path = Path(source_docx)
    target_path = Path(target_docx)

    with ZipFile(source_path) as source_zip:
        source_xml = source_zip.read(_DOCUMENT_XML)

    with ZipFile(target_path) as target_zip:
        target_infos = target_zip.infolist()
        target_payloads = {
            info.filename: target_zip.read(info.filename)
            for info in target_infos
        }

    target_payloads[_DOCUMENT_XML] = _restore_math_document_xml(
        source_xml,
        target_payloads[_DOCUMENT_XML],
    )

    with NamedTemporaryFile(
        dir=target_path.parent,
        suffix=".docx",
        delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with ZipFile(tmp_path, "w", ZIP_DEFLATED) as out_zip:
            for info in target_infos:
                out_zip.writestr(info, target_payloads[info.filename])

        tmp_path.replace(target_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
