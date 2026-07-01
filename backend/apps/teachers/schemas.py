from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ninja import Schema

from apps.reviews.schemas import DownloadLinksOut, SummaryOut


class StudentBriefOut(Schema):
    id: int
    name: str
    student_no: str
    class_name: str


class TeacherTaskSummaryOut(Schema):
    id: UUID
    student: StudentBriefOut
    status: str
    progress: int
    original_filename: str
    summary: SummaryOut
    submitted_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str


class TeacherTaskDetailOut(TeacherTaskSummaryOut):
    downloads: DownloadLinksOut


class TeacherTaskListOut(Schema):
    count: int
    page: int
    page_size: int
    items: list[TeacherTaskSummaryOut]


class TeacherStatsOut(Schema):
    student_total: int
    submitted_student_total: int
    task_total: int
    succeeded_task_total: int
    failed_task_total: int
    average_issue_total: float
    recent_tasks: list[TeacherTaskSummaryOut]
