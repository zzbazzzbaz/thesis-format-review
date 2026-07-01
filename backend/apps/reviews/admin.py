from __future__ import annotations

from django.contrib import admin
from django.db import transaction
from django import forms

from apps.accounts.models import StudentProfile
from apps.reviews.models import ReviewQuotaLedger, ReviewTask


@admin.register(ReviewTask)
class ReviewTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "status",
        "original_filename",
        "issue_error",
        "issue_warning",
        "submitted_at",
        "finished_at",
        "has_source",
        "has_marked",
        "has_issues",
    )
    list_filter = ("status", "student__teacher", "submitted_at")
    search_fields = ("id", "student__user__name", "student__student_no", "original_filename")
    readonly_fields = (
        "id",
        "source_file",
        "marked_file",
        "issues_file",
        "submitted_at",
        "started_at",
        "finished_at",
        "created_at",
        "updated_at",
    )

    @admin.display(boolean=True, description="原文")
    def has_source(self, obj: ReviewTask) -> bool:
        return bool(obj.source_file)

    @admin.display(boolean=True, description="标注")
    def has_marked(self, obj: ReviewTask) -> bool:
        return bool(obj.marked_file)

    @admin.display(boolean=True, description="JSON")
    def has_issues(self, obj: ReviewTask) -> bool:
        return bool(obj.issues_file)


class QuotaAdjustmentForm(forms.ModelForm):
    class Meta:
        model = ReviewQuotaLedger
        fields = ("student", "change", "note")

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get("student")
        change = cleaned.get("change")
        if student is not None and change is not None:
            if student.remaining_reviews + change < 0:
                raise forms.ValidationError("调整后剩余次数不能小于 0")
        return cleaned


@admin.register(ReviewQuotaLedger)
class ReviewQuotaLedgerAdmin(admin.ModelAdmin):
    form = QuotaAdjustmentForm
    list_display = ("student", "task", "change", "balance_after", "reason", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("student__user__name", "student__student_no", "note")
    readonly_fields = ("balance_after", "reason", "created_at")

    def save_model(self, request, obj: ReviewQuotaLedger, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return
        with transaction.atomic():
            student = StudentProfile.objects.select_for_update().get(pk=obj.student_id)
            new_balance = student.remaining_reviews + obj.change
            if new_balance < 0:
                raise forms.ValidationError("调整后剩余次数不能小于 0")
            student.remaining_reviews = new_balance
            student.save(update_fields=["remaining_reviews", "updated_at"])
            obj.balance_after = new_balance
            obj.reason = ReviewQuotaLedger.Reason.ADMIN_ADJUST
            super().save_model(request, obj, form, change)
