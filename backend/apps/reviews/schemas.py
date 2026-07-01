from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ninja import Schema


class SummaryOut(Schema):
    total: int
    error: int
    warning: int
    info: int


class DownloadLinksOut(Schema):
    source: str
    marked: str | None
    issues: str | None


class ReviewTaskSummaryOut(Schema):
    id: UUID
    status: str
    progress: int
    original_filename: str
    summary: SummaryOut
    submitted_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str


class ReviewTaskDetailOut(ReviewTaskSummaryOut):
    downloads: DownloadLinksOut


class ReviewTaskListOut(Schema):
    count: int
    page: int
    page_size: int
    items: list[ReviewTaskSummaryOut]


class ReviewUploadOut(Schema):
    id: UUID
    status: str
    original_filename: str
    submitted_at: datetime


class ErrorOut(Schema):
    detail: str
