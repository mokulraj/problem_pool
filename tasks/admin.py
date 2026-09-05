from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "assigned_to",
        "status",
        "due_date",
        "created_at",
    )

    list_filter = (
        "status",
        "due_date",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "project__name",
        "assigned_to__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )