from __future__ import annotations

from contextlib import suppress

from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group

from apps.accounts.models import StudentProfile, TeacherProfile, User

with suppress(NotRegistered):
    admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("个人信息", {"fields": ("name", "first_name", "last_name", "email", "role")}),
        ("权限", {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")}),
        ("重要日期", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("产品信息", {"fields": ("name", "role")}),
    )
    filter_horizontal = ("user_permissions",)
    list_display = ("username", "name", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "name")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "teacher_no", "college", "title", "student_count")
    search_fields = ("user__username", "user__name", "teacher_no", "college")

    @admin.display(description="学生数量")
    def student_count(self, obj: TeacherProfile) -> int:
        return obj.students.count()


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "student_no",
        "class_name",
        "teacher",
        "remaining_reviews",
        "updated_at",
    )
    list_filter = ("college", "major", "class_name", "teacher")
    search_fields = ("user__username", "user__name", "student_no", "class_name")
