from __future__ import annotations

from django.contrib.auth import authenticate
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.auth import JWTAuth, TokenError, decode_token, issue_token_pair, revoke_refresh_token
from apps.accounts.permissions import current_user, require_student
from apps.accounts.schemas import (
    CurrentUserOut,
    LoginIn,
    LoginOut,
    LogoutIn,
    MessageOut,
    RefreshIn,
    RefreshOut,
    StudentProfileOut,
    UserOut,
)

auth_router = Router(tags=["认证"])
user_router = Router(tags=["当前用户"], auth=JWTAuth())
student_profile_router = Router(tags=["学生端"], auth=JWTAuth())


def _user_payload(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,
    }


@auth_router.post("/login/", response=LoginOut, auth=None)
def login(request, payload: LoginIn):
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None or not user.is_active:
        raise HttpError(401, "用户名或密码错误")
    tokens = issue_token_pair(user)
    return {**tokens, "user": _user_payload(user)}


@auth_router.post("/refresh/", response=RefreshOut, auth=None)
def refresh(request, payload: RefreshIn):
    try:
        decoded = decode_token(payload.refresh, "refresh")
    except TokenError as exc:
        raise HttpError(401, str(exc)) from exc
    user_id = decoded.get("user_id")
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=user_id, is_active=True)
    except UserModel.DoesNotExist as exc:
        raise HttpError(401, "用户不存在或已停用") from exc
    return {"access": issue_token_pair(user)["access"]}


@auth_router.post("/logout/", response=MessageOut, auth=None)
def logout(request, payload: LogoutIn):
    try:
        revoke_refresh_token(payload.refresh)
    except TokenError as exc:
        raise HttpError(401, str(exc)) from exc
    return {"detail": "已退出登录"}


@user_router.get("/", response=CurrentUserOut)
def me(request):
    user = current_user(request)
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@student_profile_router.get("/", response=StudentProfileOut)
def student_profile(request):
    profile = require_student(request)
    teacher_name = None
    if profile.teacher_id:
        teacher_name = profile.teacher.user.name or profile.teacher.user.username
    return {
        "name": profile.user.name,
        "student_no": profile.student_no,
        "college": profile.college,
        "major": profile.major,
        "class_name": profile.class_name,
        "teacher": teacher_name,
        "remaining_reviews": profile.remaining_reviews,
    }
