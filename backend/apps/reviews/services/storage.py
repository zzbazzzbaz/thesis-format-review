from __future__ import annotations

import json
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from ninja.errors import HttpError

from apps.accounts.models import StudentProfile
from apps.reviews.models import ReviewQuotaLedger, ReviewTask

SOURCE_NAME = "source.docx"
MARKED_NAME = "marked.docx"
ISSUES_NAME = "issues.json"


def clean_original_filename(filename: str | None) -> str:
    if not filename:
        raise HttpError(400, "请选择 .docx 文件")
    name = filename.replace("\\", "/").split("/")[-1].strip()
    if not name:
        raise HttpError(400, "请选择 .docx 文件")
    if Path(name).suffix.lower() != ".docx":
        raise HttpError(400, "仅支持 .docx 文件")
    return name


def task_file_path(task_id, filename: str) -> str:
    return f"reviews/{task_id}/{filename}"


def save_source_file(task: ReviewTask, upload: UploadedFile) -> None:
    task.source_file.save(task_file_path(task.id, SOURCE_NAME), upload, save=False)


def save_marked_file(task: ReviewTask, content: bytes) -> None:
    task.marked_file.save(
        task_file_path(task.id, MARKED_NAME),
        ContentFile(content),
        save=False,
    )


def save_issues_file(task: ReviewTask, content: bytes) -> None:
    task.issues_file.save(
        task_file_path(task.id, ISSUES_NAME),
        ContentFile(content),
        save=False,
    )


def create_review_task(student: StudentProfile, upload: UploadedFile) -> ReviewTask:
    from django.db import transaction

    original_filename = clean_original_filename(upload.name)
    with transaction.atomic():
        locked_student = StudentProfile.objects.select_for_update().get(pk=student.pk)
        if locked_student.remaining_reviews <= 0:
            raise HttpError(400, "剩余审核次数不足")
        task = ReviewTask.objects.create(
            student=locked_student,
            original_filename=original_filename,
            status=ReviewTask.Status.PENDING,
            progress=0,
        )
        save_source_file(task, upload)
        task.save(update_fields=["source_file", "updated_at"])
        locked_student.remaining_reviews -= 1
        locked_student.save(update_fields=["remaining_reviews", "updated_at"])
        ReviewQuotaLedger.objects.create(
            student=locked_student,
            task=task,
            change=-1,
            balance_after=locked_student.remaining_reviews,
            reason=ReviewQuotaLedger.Reason.REVIEW_SUBMIT,
            note="学生提交论文审核",
        )
        return task


def summarize_issues_payload(payload: dict) -> dict[str, int]:
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return {
            "total": int(summary.get("total", 0) or 0),
            "error": int(summary.get("error", 0) or 0),
            "warning": int(summary.get("warning", 0) or 0),
            "info": int(summary.get("info", 0) or 0),
        }
    counts = {"total": 0, "error": 0, "warning": 0, "info": 0}
    issues = payload.get("issues")
    if isinstance(issues, list):
        counts["total"] = len(issues)
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            severity = issue.get("severity")
            if severity in {"error", "warning", "info"}:
                counts[severity] += 1
    return counts


def parse_issues_summary(content: bytes) -> dict[str, int]:
    payload = json.loads(content.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("issues payload must be a JSON object")
    return summarize_issues_payload(payload)
