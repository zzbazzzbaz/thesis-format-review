from __future__ import annotations

from ninja.errors import HttpError

from apps.accounts.models import StudentProfile, TeacherProfile, User


def current_user(request) -> User:
    user = request.auth
    if not user or not user.is_active:
        raise HttpError(401, "请先登录")
    return user


def require_role(request, role: str) -> User:
    user = current_user(request)
    if user.role != role:
        raise HttpError(403, "无权访问该资源")
    return user


def require_student(request) -> StudentProfile:
    user = require_role(request, User.Role.STUDENT)
    try:
        return user.student_profile
    except StudentProfile.DoesNotExist as exc:
        raise HttpError(403, "学生资料未配置") from exc


def require_teacher(request) -> TeacherProfile:
    user = require_role(request, User.Role.TEACHER)
    try:
        return user.teacher_profile
    except TeacherProfile.DoesNotExist as exc:
        raise HttpError(403, "教师资料未配置") from exc
