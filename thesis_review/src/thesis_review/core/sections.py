"""基于文档流的语义分区。"""
from __future__ import annotations

import re
from collections.abc import Iterable

from pydantic import BaseModel

from thesis_review.core.models import DocumentBlock, DocumentModel, ParagraphBlock


class SectionRange(BaseModel):
    name: str
    start: int
    end: int
    block_ids: set[str]


_TOC_ENTRY_RE = re.compile(
    r"^(?:"
    r"摘[ 　]*要|ABSTRACT|参考[ 　]*文献|致[ 　]*谢|附[ 　]*录|"
    r"第[一二三四五六七八九十\d]+章 *.+|\d+(?:\.\d+){1,2} *.+"
    r")\t\d+\s*$",
    re.IGNORECASE,
)
_BODY_CHAPTER_RE = re.compile(r"^(?:第[一二三四五六七八九十\d]+章).+")


def norm_text(text: str) -> str:
    return (
        text.replace(" ", "")
        .replace("\t", "")
        .replace("　", "")
        .replace("：", "")
        .replace(":", "")
        .strip()
    )


def _paragraphs(document: DocumentModel) -> list[ParagraphBlock]:
    return [block for block in document.blocks if block.kind == "paragraph"]


def _is_empty(para: ParagraphBlock) -> bool:
    return not para.text.strip()


def is_toc_title(para: ParagraphBlock) -> bool:
    return norm_text(para.text) == "目录"


def is_toc_entry(text: str) -> bool:
    return bool(_TOC_ENTRY_RE.match(text))


def is_body_chapter(para: ParagraphBlock) -> bool:
    text = para.text.strip()
    if "\t" in text:
        return False
    return bool(_BODY_CHAPTER_RE.match(text))


def is_body_start_candidate(para: ParagraphBlock) -> bool:
    if is_body_chapter(para):
        return True
    if para.outline_level != 0:
        return False
    normalized = norm_text(para.text)
    return normalized not in {
        "摘要",
        "ABSTRACT",
        "目录",
        "参考文献",
        "致谢",
        "附录",
    }


def is_references_title_candidate(para: ParagraphBlock) -> bool:
    text = para.text.strip()
    if "\t" in text:
        return False
    normalized = norm_text(text)
    return normalized == "参考文献" or (
        "参考" in normalized and "文献" in normalized
    )


def _find_first(
    paragraphs: list[ParagraphBlock],
    names: set[str],
    start: int = 0,
    case_sensitive: bool = True,
) -> int | None:
    expected = names if case_sensitive else {name.lower() for name in names}
    for idx, para in enumerate(paragraphs):
        if para.flow_index < start:
            continue
        text = norm_text(para.text)
        candidate = text if case_sensitive else text.lower()
        if candidate in expected:
            return idx
    return None


def _find_toc_end(paragraphs: list[ParagraphBlock], title_idx: int) -> int:
    idx = title_idx + 1
    while idx < len(paragraphs) and _is_empty(paragraphs[idx]):
        idx += 1
    while idx < len(paragraphs) and is_toc_entry(paragraphs[idx].text):
        idx += 1
    return paragraphs[idx].flow_index if idx < len(paragraphs) else len(paragraphs)


def _range(
    name: str,
    blocks: list[DocumentBlock],
    start: int,
    end: int,
) -> SectionRange:
    return SectionRange(
        name=name,
        start=start,
        end=end,
        block_ids={
            block.id for block in blocks
            if start <= block.flow_index < end
        },
    )


def detect_sections(document: DocumentModel) -> dict[str, SectionRange]:
    blocks = document.blocks
    paragraphs = _paragraphs(document)
    sections: dict[str, SectionRange] = {}
    if not blocks:
        return sections

    toc_idx = next(
        (i for i, para in enumerate(paragraphs) if is_toc_title(para)),
        None,
    )
    toc_start = paragraphs[toc_idx].flow_index if toc_idx is not None else None
    toc_end = _find_toc_end(paragraphs, toc_idx) if toc_idx is not None else None

    body_start = None
    for para in paragraphs:
        if toc_end is not None and para.flow_index < toc_end:
            continue
        if is_body_start_candidate(para):
            body_start = para.flow_index
            break

    ref_idx = next(
        (
            i for i, para in enumerate(paragraphs)
            if para.flow_index >= (body_start or 0)
            and is_references_title_candidate(para)
        ),
        None,
    )
    ref_flow = paragraphs[ref_idx].flow_index if ref_idx is not None else 0
    thanks_idx = _find_first(paragraphs, {"致谢"}, start=ref_flow)
    thanks_flow = paragraphs[thanks_idx].flow_index if thanks_idx is not None else 0
    appendix_idx = _find_first(paragraphs, {"附录"}, start=thanks_flow)
    abstract_cn_idx = _find_first(paragraphs, {"摘要"})
    abstract_en_idx = _find_first(paragraphs, {"ABSTRACT"}, case_sensitive=False)

    doc_start = blocks[0].flow_index
    doc_end = blocks[-1].flow_index + 1

    abstract_cn_start = (
        paragraphs[abstract_cn_idx].flow_index
        if abstract_cn_idx is not None
        else None
    )
    abstract_en_start = (
        paragraphs[abstract_en_idx].flow_index
        if abstract_en_idx is not None
        else None
    )
    ref_start = (
        paragraphs[ref_idx].flow_index if ref_idx is not None else None
    )
    thanks_start = (
        paragraphs[thanks_idx].flow_index if thanks_idx is not None else None
    )
    appendix_start = (
        paragraphs[appendix_idx].flow_index
        if appendix_idx is not None
        else None
    )

    abstract_start = abstract_cn_start or abstract_en_start
    abstract_end = toc_start or doc_end

    if abstract_start is not None:
        sections["cover"] = _range(
            "cover", blocks, doc_start, abstract_start
        )
        sections["abstract"] = _range(
            "abstract",
            blocks,
            abstract_start,
            abstract_end,
        )
    if abstract_cn_start is not None:
        sections["abstract-chinese"] = _range(
            "abstract-chinese",
            blocks,
            abstract_cn_start,
            abstract_en_start or toc_start or doc_end,
        )
    if abstract_en_start is not None:
        sections["abstract-english"] = _range(
            "abstract-english", blocks, abstract_en_start, toc_start or doc_end
        )
    if toc_start is not None and toc_end is not None:
        sections["table-of-contents"] = _range(
            "table-of-contents",
            blocks,
            toc_start,
            toc_end,
        )
    if body_start is not None:
        sections["main-text"] = _range(
            "main-text", blocks, body_start, ref_start or doc_end
        )
    if ref_start is not None:
        sections["references"] = _range(
            "references",
            blocks,
            ref_start,
            thanks_start or appendix_start or doc_end,
        )
    if thanks_start is not None:
        sections["acknowledgements"] = _range(
            "acknowledgements", blocks, thanks_start, appendix_start or doc_end
        )
    if appendix_start is not None:
        sections["appendix"] = _range("appendix", blocks, appendix_start, doc_end)

    return sections


def blocks_in_range(
    document: DocumentModel,
    section: SectionRange,
) -> Iterable[DocumentBlock]:
    return (
        block for block in document.blocks
        if section.start <= block.flow_index < section.end
    )


def paragraphs_in_range(
    document: DocumentModel,
    section: SectionRange,
) -> Iterable[ParagraphBlock]:
    return (
        block for block in blocks_in_range(document, section)
        if block.kind == "paragraph"
    )
