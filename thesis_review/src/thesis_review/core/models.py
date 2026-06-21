"""引擎无关的核心数据模型，是各层之间唯一的耦合点。"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

BlockKind = Literal["paragraph", "table", "image"]
TargetKind = Literal["block", "run"]
IssueCategory = Literal["format", "structure", "ai"]
IssueSeverity = Literal["error", "warning", "info"]
TabStopAlignment = Literal["left", "center", "right", "decimal", "unknown"]
PageNumberFormat = Literal["arabic", "roman", "unknown"]


class RunSpan(BaseModel):
    id: str
    text: str
    run_index: int
    font_east_asian: str | None
    font_latin: str | None
    size_pt: float | None
    bold: bool
    italic: bool
    superscript: bool = False


class FormattedTextRun(BaseModel):
    text: str
    run_index: int
    font_east_asian: str | None = None
    font_latin: str | None = None
    size_pt: float | None = None
    bold: bool = False
    italic: bool = False


class HeaderFooterParagraph(BaseModel):
    text: str
    paragraph_index: int
    alignment: str | None = None
    runs: list[FormattedTextRun] = []
    has_page_number_field: bool = False
    page_number_text: str | None = None
    page_number_format: PageNumberFormat | None = None


class TabStopInfo(BaseModel):
    position_mm: float | None = None
    alignment: TabStopAlignment = "unknown"


class BlockBase(BaseModel):
    id: str
    kind: BlockKind
    flow_index: int
    type_index: int
    page_style_name: str | None = None


class ParagraphBlock(BlockBase):
    kind: Literal["paragraph"] = "paragraph"
    text: str
    style_name: str | None
    outline_level: int | None
    alignment: str | None
    line_spacing: float | None
    first_line_indent_chars: float | None
    page_break_before: bool = False
    is_empty: bool = False
    runs: list[RunSpan]
    contains_math: bool = False
    math_object_count: int = 0
    tab_stops: list[TabStopInfo] = []


class TableBlock(BlockBase):
    kind: Literal["table"] = "table"
    row_count: int | None = None
    column_count: int | None = None
    text: str = ""


class ImageBlock(BlockBase):
    kind: Literal["image"] = "image"
    name: str | None = None
    alt_text: str | None = None
    width_mm: float | None = None
    height_mm: float | None = None


DocumentBlock = Annotated[
    ParagraphBlock | TableBlock | ImageBlock,
    Field(discriminator="kind"),
]


class PageStyleInfo(BaseModel):
    name: str
    width_mm: float | None = None
    height_mm: float | None = None
    margin_top_mm: float | None = None
    margin_bottom_mm: float | None = None
    margin_left_mm: float | None = None
    margin_right_mm: float | None = None
    header_text: str | None = None
    footer_text: str | None = None
    header_paragraphs: list[HeaderFooterParagraph] = []
    footer_paragraphs: list[HeaderFooterParagraph] = []


class DocumentModel(BaseModel):
    source_docx: str
    blocks: list[DocumentBlock]
    page_styles: list[PageStyleInfo] = []


class Location(BaseModel):
    target: TargetKind
    block_id: str
    block_kind: BlockKind
    flow_index: int
    run_id: str | None = None
    run_index: int | None = None

    @model_validator(mode="after")
    def validate_location(self) -> "Location":
        if self.target == "run":
            if self.block_kind != "paragraph":
                raise ValueError("run target only belongs to paragraph block")
            if self.run_id is None or self.run_index is None:
                raise ValueError("run target requires run_id and run_index")
        elif self.run_id is not None or self.run_index is not None:
            raise ValueError("block target must not include run fields")
        return self


class Issue(BaseModel):
    rule_id: str
    category: IssueCategory
    severity: IssueSeverity
    message: str
    expected: str | None = None
    actual: str | None = None
    location: Location
