from __future__ import annotations

import pytest
from django.test import Client

from apps.accounts.auth import issue_token_pair
from apps.accounts.models import StudentProfile, TeacherProfile, User


@pytest.mark.django_db
def test_login_and_current_user():
    user = User.objects.create_user(
        username="student",
        password="pass12345",
        name="张三",
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(user=user, student_no="20260001", remaining_reviews=2)

    client = Client()
    response = client.post(
        "/api/auth/login/",
        data={"username": "student", "password": "pass12345"},
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["role"] == "student"
    assert payload["access"]
    assert payload["refresh"]

    response = client.get(
        "/api/me/",
        HTTP_AUTHORIZATION=f"Bearer {payload['access']}",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "张三"


@pytest.mark.django_db
def test_student_profile_requires_student_role():
    teacher_user = User.objects.create_user(
        username="teacher",
        password="pass12345",
        name="李老师",
        role=User.Role.TEACHER,
    )
    TeacherProfile.objects.create(user=teacher_user, teacher_no="T001")
    token = issue_token_pair(teacher_user)["access"]

    response = Client().get(
        "/api/student/profile/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_refresh_and_logout_revokes_refresh_token():
    user = User.objects.create_user(
        username="student",
        password="pass12345",
        name="张三",
        role=User.Role.STUDENT,
    )
    refresh = issue_token_pair(user)["refresh"]
    client = Client()

    response = client.post(
        "/api/auth/refresh/",
        data={"refresh": refresh},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["access"]

    response = client.post(
        "/api/auth/logout/",
        data={"refresh": refresh},
        content_type="application/json",
    )
    assert response.status_code == 200

    response = client.post(
        "/api/auth/refresh/",
        data={"refresh": refresh},
        content_type="application/json",
    )
    assert response.status_code == 401
