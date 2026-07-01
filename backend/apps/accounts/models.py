from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "学生"
        TEACHER = "teacher", "教师"
        ADMIN = "admin", "管理员"

    name = models.CharField("姓名", max_length=80, blank=True)
    role = models.CharField(
        "角色",
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    def __str__(self) -> str:
        return self.name or self.username


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name="用户",
    )
    teacher_no = models.CharField("教师工号", max_length=40, unique=True)
    college = models.CharField("学院", max_length=120, blank=True)
    title = models.CharField("职称", max_length=80, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "教师资料"
        verbose_name_plural = "教师资料"

    def __str__(self) -> str:
        return f"{self.user}（{self.teacher_no}）"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name="用户",
    )
    student_no = models.CharField("学号", max_length=40, unique=True)
    college = models.CharField("学院", max_length=120, blank=True)
    major = models.CharField("专业", max_length=120, blank=True)
    class_name = models.CharField("班级", max_length=120, blank=True)
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        related_name="students",
        null=True,
        blank=True,
        verbose_name="指导教师",
    )
    remaining_reviews = models.PositiveIntegerField("剩余审核次数", default=3)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学生资料"
        verbose_name_plural = "学生资料"

    def __str__(self) -> str:
        return f"{self.user}（{self.student_no}）"


class RevokedToken(models.Model):
    jti = models.CharField("JWT ID", max_length=64, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="revoked_tokens",
        verbose_name="用户",
    )
    expires_at = models.DateTimeField("过期时间")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "已注销令牌"
        verbose_name_plural = "已注销令牌"

    def __str__(self) -> str:
        return self.jti
