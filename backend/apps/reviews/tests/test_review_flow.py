from __future__ import annotations

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings

from apps.accounts.auth import issue_token_pair
from apps.accounts.models import StudentProfile, TeacherProfile, User
from apps.reviews.models import ReviewQuotaLedger, ReviewTask
from apps.reviews.services.executor import claim_next_pending_task, execute_task
from apps.reviews.services.storage import create_review_task
from apps.reviews.services.thesis_review_client import ThesisReviewClientError


class SuccessClient:
    def review_docx(self, path: str, filename: str = "source.docx"):
        class Artifacts:
            marked_docx = b"marked docx"
            issues_json = b'{"summary":{"total":2,"error":1,"warning":1,"info":0},"issues":[]}'

        return Artifacts()


class FailureClient:
    def review_docx(self, path: str, filename: str = "source.docx"):
        raise ThesisReviewClientError("审核服务暂不可用")


@pytest.fixture
def student():
    user = User.objects.create_user(
        username="student",
        password="pass12345",
        name="张三",
        role=User.Role.STUDENT,
    )
    return StudentProfile.objects.create(
        user=user,
        student_no="20260001",
        remaining_reviews=1,
    )


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/thesis-review-backend-test-media")
def test_create_review_task_decrements_quota_and_writes_ledger(student):
    upload = SimpleUploadedFile(
        "paper.docx",
        b"docx bytes",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    task = create_review_task(student, upload)
    student.refresh_from_db()

    assert task.status == ReviewTask.Status.PENDING
    assert task.source_file.name == f"reviews/{task.id}/source.docx"
    assert student.remaining_reviews == 0
    ledger = ReviewQuotaLedger.objects.get(task=task)
    assert ledger.change == -1
    assert ledger.balance_after == 0


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/thesis-review-backend-test-media")
def test_create_review_task_rejects_when_quota_empty(student):
    student.remaining_reviews = 0
    student.save(update_fields=["remaining_reviews"])
    upload = SimpleUploadedFile("paper.docx", b"docx bytes")

    with pytest.raises(Exception):
        create_review_task(student, upload)

    assert ReviewTask.objects.count() == 0


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/thesis-review-backend-test-media")
def test_worker_claims_and_executes_success(student):
    task = create_review_task(student, SimpleUploadedFile("paper.docx", b"docx bytes"))

    claimed = claim_next_pending_task()
    assert claimed.id == task.id
    result = execute_task(task.id, client=SuccessClient())
    result.refresh_from_db()

    assert result.status == ReviewTask.Status.SUCCEEDED
    assert result.progress == 100
    assert result.issue_total == 2
    assert result.issue_error == 1
    assert result.marked_file.name.endswith("/marked.docx")
    assert result.issues_file.name.endswith("/issues.json")


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/thesis-review-backend-test-media")
def test_worker_records_safe_failure(student):
    task = create_review_task(student, SimpleUploadedFile("paper.docx", b"docx bytes"))
    claim_next_pending_task()

    result = execute_task(task.id, client=FailureClient())
    result.refresh_from_db()

    assert result.status == ReviewTask.Status.FAILED
    assert result.error_message == "审核服务暂不可用"


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/thesis-review-backend-test-media")
def test_student_api_upload_list_detail_and_download(student):
    token = issue_token_pair(student.user)["access"]
    client = Client()

    response = client.post(
        "/api/student/review-tasks/",
        data={"file": BytesIO(b"docx bytes")},
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 400

    file = SimpleUploadedFile("paper.docx", b"docx bytes")
    response = client.post(
        "/api/student/review-tasks/",
        data={"file": file},
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200
    task_id = response.json()["id"]

    response = client.get(
        "/api/student/review-tasks/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = client.get(
        f"/api/student/review-tasks/{task_id}/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200
    assert response.json()["downloads"]["source"].endswith("/download/source/")


@pytest.mark.django_db
def test_student_cannot_see_other_student_task():
    first = User.objects.create_user(username="s1", password="pass12345", role=User.Role.STUDENT)
    second = User.objects.create_user(username="s2", password="pass12345", role=User.Role.STUDENT)
    first_profile = StudentProfile.objects.create(user=first, student_no="S1", remaining_reviews=1)
    StudentProfile.objects.create(user=second, student_no="S2", remaining_reviews=1)
    task = ReviewTask.objects.create(student=first_profile, original_filename="paper.docx")
    token = issue_token_pair(second)["access"]

    response = Client().get(
        f"/api/student/review-tasks/{task.id}/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 404
