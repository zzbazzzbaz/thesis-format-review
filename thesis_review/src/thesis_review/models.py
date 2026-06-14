"""引擎无关的核心数据模型，是各层之间唯一的耦合点。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator

LocationKind = Literal["paragraph", "run"]
IssueCategory = Literal["format", "structure", "ai"]
IssueSeverity = Literal["error", "warning", "info"]


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
    kind: LocationKind
    block_id: str
    paragraph_index: int
    run_id: str | None = None
    run_index: int | None = None

    @model_validator(mode="after")
    def validate_run_location(self) -> "Location":
        if self.kind == "run" and (self.run_id is None or self.run_index is None):
            raise ValueError("run location requires run_id and run_index")
        if self.kind == "paragraph" and (
            self.run_id is not None or self.run_index is not None
        ):
            raise ValueError("paragraph location must not include run_id or run_index")
        return self


class Issue(BaseModel):
    rule_id: str
    category: IssueCategory
    severity: IssueSeverity
    message: str
    expected: str | None = None
    actual: str | None = None
    location: Location
