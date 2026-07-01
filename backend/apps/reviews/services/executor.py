from __future__ import annotations

import logging
from json import JSONDecodeError

from django.db import transaction
from django.utils import timezone

from apps.reviews.models import ReviewTask
from apps.reviews.services.storage import (
    parse_issues_summary,
    save_issues_file,
    save_marked_file,
)
from apps.reviews.services.thesis_review_client import (
    ThesisReviewClient,
    ThesisReviewClientError,
)

logger = logging.getLogger(__name__)


def claim_next_pending_task() -> ReviewTask | None:
    with transaction.atomic():
        task = (
            ReviewTask.objects.select_for_update()
            .filter(status=ReviewTask.Status.PENDING)
            .order_by("submitted_at")
            .first()
        )
        if task is None:
            return None
        task.status = ReviewTask.Status.RUNNING
        task.progress = 20
        task.started_at = timezone.now()
        task.error_message = ""
        task.save(update_fields=["status", "progress", "started_at", "error_message", "updated_at"])
        return task


def execute_task(task_id, client: ThesisReviewClient | None = None) -> ReviewTask:
    client = client or ThesisReviewClient()
    task = ReviewTask.objects.get(pk=task_id)
    try:
        if not task.source_file:
            raise RuntimeError("missing source file")
        artifacts = client.review_docx(task.source_file.path, filename=task.original_filename)
        task.progress = 90
        save_marked_file(task, artifacts.marked_docx)
        save_issues_file(task, artifacts.issues_json)
        summary = parse_issues_summary(artifacts.issues_json)
        task.issue_total = summary["total"]
        task.issue_error = summary["error"]
        task.issue_warning = summary["warning"]
        task.issue_info = summary["info"]
        task.status = ReviewTask.Status.SUCCEEDED
        task.progress = 100
        task.error_message = ""
        task.finished_at = timezone.now()
        task.save(
            update_fields=[
                "marked_file",
                "issues_file",
                "issue_total",
                "issue_error",
                "issue_warning",
                "issue_info",
                "status",
                "progress",
                "error_message",
                "finished_at",
                "updated_at",
            ]
        )
    except Exception as exc:
        _mark_failed(task, _safe_error_message(exc))
        logger.info("review task failed: %s", task.pk, exc_info=exc)
    return task


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, ThesisReviewClientError):
        return exc.public_message
    if isinstance(exc, (JSONDecodeError, UnicodeDecodeError, ValueError)):
        return "审核结果解析失败"
    return "审核任务处理失败"


def _mark_failed(task: ReviewTask, message: str) -> None:
    task.status = ReviewTask.Status.FAILED
    task.progress = 100
    task.error_message = message[:500]
    task.finished_at = timezone.now()
    task.save(update_fields=["status", "progress", "error_message", "finished_at", "updated_at"])
