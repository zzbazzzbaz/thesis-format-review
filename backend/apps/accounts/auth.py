from __future__ import annotations

from datetime import datetime, timedelta, timezone as datetime_timezone
from typing import Any
from uuid import uuid4

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from jwt import InvalidTokenError
from ninja.security import HttpBearer

from apps.accounts.models import RevokedToken, User


class TokenError(ValueError):
    pass


def _now() -> datetime:
    return timezone.now()


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def make_token(user: User, token_type: str, lifetime_seconds: int) -> str:
    issued_at = _now()
    expires_at = issued_at + timedelta(seconds=lifetime_seconds)
    payload = {
        "type": token_type,
        "user_id": user.pk,
        "jti": uuid4().hex,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return _encode(payload)


def issue_token_pair(user: User) -> dict[str, str]:
    return {
        "access": make_token(user, "access", settings.JWT_ACCESS_TOKEN_SECONDS),
        "refresh": make_token(user, "refresh", settings.JWT_REFRESH_TOKEN_SECONDS),
    }


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except InvalidTokenError as exc:
        raise TokenError("令牌无效或已过期") from exc
    if payload.get("type") != expected_type:
        raise TokenError("令牌类型不正确")
    jti = payload.get("jti")
    if jti and RevokedToken.objects.filter(jti=jti).exists():
        raise TokenError("令牌已注销")
    return payload


def get_user_from_token(token: str, expected_type: str = "access") -> User:
    payload = decode_token(token, expected_type)
    user_id = payload.get("user_id")
    if not user_id:
        raise TokenError("令牌缺少用户信息")
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=user_id, is_active=True)
    except UserModel.DoesNotExist as exc:
        raise TokenError("用户不存在或已停用") from exc
    return user


def revoke_refresh_token(token: str) -> None:
    payload = decode_token(token, "refresh")
    user = get_user_from_token(token, "refresh")
    expires_at = datetime.fromtimestamp(payload["exp"], tz=datetime_timezone.utc)
    RevokedToken.objects.get_or_create(
        jti=payload["jti"],
        defaults={"user": user, "expires_at": expires_at},
    )


class JWTAuth(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            return get_user_from_token(token, "access")
        except TokenError:
            return None
