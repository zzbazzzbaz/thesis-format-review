from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from apps.accounts.models import StudentProfile


class ReviewTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "等待审核"
        RUNNING = "running", "正在审核"
        SUCCEEDED = "succeeded", "审核完成"
        FAILED = "failed", "审核失败"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="review_tasks",
        verbose_name="学生",
    )
    original_filename = models.CharField("原始文件名", max_length=255)
    source_file = models.FileField("原始 Word", upload_to="", blank=True)
    marked_file = models.FileField("标注 Word", upload_to="", blank=True)
    issues_file = models.FileField("审核 JSON", upload_to="", blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    progress = models.PositiveSmallIntegerField("进度", default=0)
    error_message = models.CharField("失败原因", max_length=500, blank=True)
    issue_total = models.PositiveIntegerField("问题总数", default=0)
    issue_error = models.PositiveIntegerField("错误数", default=0)
    issue_warning = models.PositiveIntegerField("警告数", default=0)
    issue_info = models.PositiveIntegerField("提示数", default=0)
    submitted_at = models.DateTimeField("提交时间", default=timezone.now)
    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "审核任务"
        verbose_name_plural = "审核任务"
        ordering = ("-submitted_at",)
        indexes = [
            models.Index(fields=["status", "submitted_at"]),
            models.Index(fields=["student", "-submitted_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.original_filename} - {self.get_status_display()}"


class ReviewQuotaLedger(models.Model):
    class Reason(models.TextChoices):
        REVIEW_SUBMIT = "review_submit", "提交审核扣减"
        ADMIN_ADJUST = "admin_adjust", "管理员调整"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="quota_ledgers",
        verbose_name="学生",
    )
    task = models.ForeignKey(
        ReviewTask,
        on_delete=models.SET_NULL,
        related_name="quota_ledgers",
        null=True,
        blank=True,
        verbose_name="审核任务",
    )
    change = models.IntegerField("次数变化")
    balance_after = models.PositiveIntegerField("变更后余额")
    reason = models.CharField("原因", max_length=40, choices=Reason.choices)
    note = models.CharField("备注", max_length=255, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "次数流水"
        verbose_name_plural = "次数流水"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.student} {self.change:+d} -> {self.balance_after}"
