from __future__ import annotations

from datetime import datetime
from typing import Literal

from ninja import Schema


class UserOut(Schema):
    id: int
    username: str
    name: str
    role: Literal["student", "teacher", "admin"]


class LoginIn(Schema):
    username: str
    password: str


class LoginOut(Schema):
    access: str
    refresh: str
    user: UserOut


class RefreshIn(Schema):
    refresh: str


class RefreshOut(Schema):
    access: str


class LogoutIn(Schema):
    refresh: str


class MessageOut(Schema):
    detail: str


class StudentProfileOut(Schema):
    name: str
    student_no: str
    college: str
    major: str
    class_name: str
    teacher: str | None
    remaining_reviews: int


class CurrentUserOut(Schema):
    id: int
    username: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
