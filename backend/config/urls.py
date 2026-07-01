"""URL routing for the product backend."""
from __future__ import annotations

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from ninja import NinjaAPI

from apps.accounts.api import auth_router, student_profile_router, user_router
from apps.reviews.api import student_reviews_router
from apps.teachers.api import teacher_router

api = NinjaAPI(title="毕业设计格式审核产品后端", version="0.1.0")


@api.get("/healthz", auth=None)
def api_healthz(request):
    return {"status": "ok"}


def healthz(request):
    return JsonResponse({"status": "ok"})


api.add_router("/auth/", auth_router)
api.add_router("/me/", user_router)
api.add_router("/student/profile/", student_profile_router)
api.add_router("/student/review-tasks/", student_reviews_router)
api.add_router("/teacher/", teacher_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),
    path("api/", api.urls),
]
