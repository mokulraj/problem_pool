from django.contrib import admin

from .models import Task


# =========================================================
# TASK BULK ACTIONS
# =========================================================

@admin.action(description="Mark selected tasks as pending")
def mark_tasks_pending(modeladmin, request, queryset):
    queryset.update(
        status=Task.Status.PENDING,
    )


@admin.action(description="Mark selected tasks as in progress")
def mark_tasks_in_progress(modeladmin, request, queryset):
    queryset.update(
        status=Task.Status.IN_PROGRESS,
    )


@admin.action(description="Mark selected tasks as completed")
def mark_tasks_completed(modeladmin, request, queryset):
    queryset.update(
        status=Task.Status.COMPLETED,
    )


# =========================================================
# TASK ADMIN
# =========================================================

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "project",
        "assigned_to",
        "status",
        "due_date",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "due_date",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "description",
        "project__name",
        "assigned_to__username",
        "assigned_to__email",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    actions = (
        mark_tasks_pending,
        mark_tasks_in_progress,
        mark_tasks_completed,
    )

    list_per_page = 25