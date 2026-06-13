"""引擎无关的核心数据模型，是各层之间唯一的耦合点。"""
from __future__ import annotations

from pydantic import BaseModel


class RunSpan(BaseModel):
    id: str
    text: str
    run_index: int
    font_east_asian: str | None
    font_latin: str | None
    size_pt: float | None
    bold: bool
    italic: bool


class ParagraphBlock(BaseModel):
    id: str
    text: str
    paragraph_index: int
    style_name: str | None
    outline_level: int | None
    alignment: str | None
    line_spacing: float | None
    first_line_indent_chars: float | None
    runs: list[RunSpan]


class DocumentModel(BaseModel):
    source_docx: str
    paragraphs: list[ParagraphBlock]


class Location(BaseModel):
    kind: str
    block_id: str
    paragraph_index: int
    run_id: str | None = None
    run_index: int | None = None


class Issue(BaseModel):
    rule_id: str
    category: str
    severity: str
    message: str
    expected: str | None = None
    actual: str | None = None
    location: Location
