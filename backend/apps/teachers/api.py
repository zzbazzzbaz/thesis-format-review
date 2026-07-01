from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from django.db.models import Avg, Count, Q
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.auth import JWTAuth
from apps.accounts.permissions import require_teacher
from apps.reviews.api import _artifact_response
from apps.reviews.models import ReviewTask
from apps.teachers.schemas import (
    TeacherStatsOut,
    TeacherTaskDetailOut,
    TeacherTaskListOut,
)

teacher_router = Router(tags=["教师端"], auth=JWTAuth())


def _student_payload(student) -> dict:
    return {
        "id": student.id,
        "name": student.user.name,
        "student_no": student.student_no,
        "class_name": student.class_name,
    }


def _summary(task: ReviewTask) -> dict:
    return {
        "total": task.issue_total,
        "error": task.issue_error,
        "warning": task.issue_warning,
        "info": task.issue_info,
    }


def _task_payload(task: ReviewTask) -> dict:
    return {
        "id": task.id,
        "student": _student_payload(task.student),
        "status": task.status,
        "progress": task.progress,
        "original_filename": task.original_filename,
        "summary": _summary(task),
        "submitted_at": task.submitted_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "error_message": task.error_message,
    }


def _downloads(task: ReviewTask) -> dict:
    base = f"/api/teacher/review-tasks/{task.id}/download"
    return {
        "source": f"{base}/source/",
        "marked": f"{base}/marked/" if task.status == ReviewTask.Status.SUCCEEDED else None,
        "issues": f"{base}/issues/" if task.status == ReviewTask.Status.SUCCEEDED else None,
    }


def _task_queryset(teacher):
    return (
        ReviewTask.objects.filter(student__teacher=teacher)
        .select_related("student", "student__user")
        .order_by("-submitted_at")
    )


def _teacher_task_or_404(teacher, task_id: UUID) -> ReviewTask:
    try:
        return _task_queryset(teacher).get(pk=task_id)
    except ReviewTask.DoesNotExist as exc:
        raise HttpError(404, "任务不存在") from exc


def _day_start(value: date) -> datetime:
    return timezone.make_aware(datetime.combine(value, time.min))


def _day_end(value: date) -> datetime:
    return timezone.make_aware(datetime.combine(value, time.max))


@teacher_router.get("/review-tasks/", response=TeacherTaskListOut)
def list_student_review_tasks(
    request,
    page: int = 1,
    page_size: int = 20,
    student_no: str | None = None,
    student_name: str | None = None,
    status: str | None = None,
    submitted_from: date | None = None,
    submitted_to: date | None = None,
):
    teacher = require_teacher(request)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    qs = _task_queryset(teacher)
    if student_no:
        qs = qs.filter(student__student_no__icontains=student_no)
    if student_name:
        qs = qs.filter(Q(student__user__name__icontains=student_name) | Q(student__user__username__icontains=student_name))
    if status:
        if status not in ReviewTask.Status.values:
            raise HttpError(400, "任务状态无效")
        qs = qs.filter(status=status)
    if submitted_from:
        qs = qs.filter(submitted_at__gte=_day_start(submitted_from))
    if submitted_to:
        qs = qs.filter(submitted_at__lte=_day_end(submitted_to))
    count = qs.count()
    start = (page - 1) * page_size
    items = [_task_payload(task) for task in qs[start : start + page_size]]
    return {"count": count, "page": page, "page_size": page_size, "items": items}


@teacher_router.get("/review-tasks/{task_id}/", response=TeacherTaskDetailOut)
def get_student_review_task(request, task_id: UUID):
    teacher = require_teacher(request)
    task = _teacher_task_or_404(teacher, task_id)
    return {**_task_payload(task), "downloads": _downloads(task)}


@teacher_router.get("/review-tasks/{task_id}/download/{artifact}/")
def download_student_review_artifact(request, task_id: UUID, artifact: str):
    teacher = require_teacher(request)
    task = _teacher_task_or_404(teacher, task_id)
    return _artifact_response(task, artifact)


@teacher_router.get("/stats/", response=TeacherStatsOut)
def teacher_stats(request):
    teacher = require_teacher(request)
    students = teacher.students.all()
    tasks = _task_queryset(teacher)
    aggregates = tasks.aggregate(
        task_total=Count("id"),
        average_issue_total=Avg("issue_total"),
    )
    recent_tasks = [_task_payload(task) for task in tasks[:10]]
    return {
        "student_total": students.count(),
        "submitted_student_total": students.filter(review_tasks__isnull=False).distinct().count(),
        "task_total": aggregates["task_total"] or 0,
        "succeeded_task_total": tasks.filter(status=ReviewTask.Status.SUCCEEDED).count(),
        "failed_task_total": tasks.filter(status=ReviewTask.Status.FAILED).count(),
        "average_issue_total": float(aggregates["average_issue_total"] or 0),
        "recent_tasks": recent_tasks,
    }
