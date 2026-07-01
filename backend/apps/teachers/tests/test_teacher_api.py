from __future__ import annotations

import pytest
from django.test import Client

from apps.accounts.auth import issue_token_pair
from apps.accounts.models import StudentProfile, TeacherProfile, User
from apps.reviews.models import ReviewTask


@pytest.fixture
def teacher_data():
    teacher_user = User.objects.create_user(
        username="teacher",
        password="pass12345",
        name="李老师",
        role=User.Role.TEACHER,
    )
    other_teacher_user = User.objects.create_user(
        username="teacher2",
        password="pass12345",
        name="王老师",
        role=User.Role.TEACHER,
    )
    teacher = TeacherProfile.objects.create(user=teacher_user, teacher_no="T001")
    other_teacher = TeacherProfile.objects.create(user=other_teacher_user, teacher_no="T002")
    student_user = User.objects.create_user(username="student", role=User.Role.STUDENT)
    other_student_user = User.objects.create_user(username="student2", role=User.Role.STUDENT)
    student = StudentProfile.objects.create(
        user=student_user,
        student_no="S001",
        teacher=teacher,
        remaining_reviews=1,
    )
    other_student = StudentProfile.objects.create(
        user=other_student_user,
        student_no="S002",
        teacher=other_teacher,
        remaining_reviews=1,
    )
    task = ReviewTask.objects.create(
        student=student,
        original_filename="paper.docx",
        status=ReviewTask.Status.SUCCEEDED,
        issue_total=4,
    )
    other_task = ReviewTask.objects.create(
        student=other_student,
        original_filename="other.docx",
        status=ReviewTask.Status.SUCCEEDED,
    )
    return teacher_user, task, other_task


@pytest.mark.django_db
def test_teacher_sees_only_own_students_tasks(teacher_data):
    teacher_user, task, other_task = teacher_data
    token = issue_token_pair(teacher_user)["access"]

    response = Client().get(
        "/api/teacher/review-tasks/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert str(task.id) in ids
    assert str(other_task.id) not in ids


@pytest.mark.django_db
def test_teacher_stats_are_limited_to_own_students(teacher_data):
    teacher_user, task, _ = teacher_data
    token = issue_token_pair(teacher_user)["access"]

    response = Client().get(
        "/api/teacher/stats/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["student_total"] == 1
    assert payload["task_total"] == 1
    assert payload["succeeded_task_total"] == 1
    assert payload["average_issue_total"] == 4.0
