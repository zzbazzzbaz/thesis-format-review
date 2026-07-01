from __future__ import annotations

from pathlib import Path
from uuid import UUID

from django.http import FileResponse
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from apps.accounts.auth import JWTAuth
from apps.accounts.permissions import require_student
from apps.reviews.models import ReviewTask
from apps.reviews.schemas import ReviewTaskDetailOut, ReviewTaskListOut, ReviewUploadOut
from apps.reviews.services.storage import create_review_task

student_reviews_router = Router(tags=["学生端审核任务"], auth=JWTAuth())


def _summary(task: ReviewTask) -> dict:
    return {
        "total": task.issue_total,
        "error": task.issue_error,
        "warning": task.issue_warning,
        "info": task.issue_info,
    }


def _task_summary(task: ReviewTask) -> dict:
    return {
        "id": task.id,
        "status": task.status,
        "progress": task.progress,
        "original_filename": task.original_filename,
        "summary": _summary(task),
        "submitted_at": task.submitted_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "error_message": task.error_message,
    }


def _downloads(task: ReviewTask, prefix: str) -> dict:
    base = f"{prefix}/{task.id}/download"
    return {
        "source": f"{base}/source/",
        "marked": f"{base}/marked/" if task.status == ReviewTask.Status.SUCCEEDED else None,
        "issues": f"{base}/issues/" if task.status == ReviewTask.Status.SUCCEEDED else None,
    }


def _student_task_or_404(student, task_id: UUID) -> ReviewTask:
    try:
        return ReviewTask.objects.get(pk=task_id, student=student)
    except ReviewTask.DoesNotExist as exc:
        raise HttpError(404, "任务不存在") from exc


@student_reviews_router.post("/", response=ReviewUploadOut)
def upload_review_task(request, file: File[UploadedFile]):
    student = require_student(request)
    task = create_review_task(student, file)
    return {
        "id": task.id,
        "status": task.status,
        "original_filename": task.original_filename,
        "submitted_at": task.submitted_at,
    }


@student_reviews_router.get("/", response=ReviewTaskListOut)
def list_review_tasks(
    request,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
):
    student = require_student(request)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    qs = ReviewTask.objects.filter(student=student).order_by("-submitted_at")
    if status:
        if status not in ReviewTask.Status.values:
            raise HttpError(400, "任务状态无效")
        qs = qs.filter(status=status)
    count = qs.count()
    start = (page - 1) * page_size
    items = [_task_summary(task) for task in qs[start : start + page_size]]
    return {"count": count, "page": page, "page_size": page_size, "items": items}


@student_reviews_router.get("/{task_id}/", response=ReviewTaskDetailOut)
def get_review_task(request, task_id: UUID):
    student = require_student(request)
    task = _student_task_or_404(student, task_id)
    return {**_task_summary(task), "downloads": _downloads(task, "/api/student/review-tasks")}


@student_reviews_router.get("/{task_id}/download/{artifact}/")
def download_review_artifact(request, task_id: UUID, artifact: str):
    student = require_student(request)
    task = _student_task_or_404(student, task_id)
    return _artifact_response(task, artifact)


def _artifact_response(task: ReviewTask, artifact: str):
    if artifact == "source":
        field = task.source_file
        filename = task.original_filename
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif artifact == "marked":
        if task.status != ReviewTask.Status.SUCCEEDED:
            raise HttpError(409, "审核结果尚未生成")
        field = task.marked_file
        filename = f"{Path(task.original_filename).stem}.marked.docx"
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif artifact == "issues":
        if task.status != ReviewTask.Status.SUCCEEDED:
            raise HttpError(409, "审核结果尚未生成")
        field = task.issues_file
        filename = f"{Path(task.original_filename).stem}.issues.json"
        content_type = "application/json"
    else:
        raise HttpError(404, "文件不存在")
    if not field:
        raise HttpError(404, "文件不存在")
    try:
        return FileResponse(
            field.open("rb"),
            as_attachment=True,
            filename=filename,
            content_type=content_type,
        )
    except FileNotFoundError as exc:
        raise HttpError(404, "文件不存在") from exc
