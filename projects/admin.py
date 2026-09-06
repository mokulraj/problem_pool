from django.contrib import admin

from .models import Project


# =========================================================
# PROJECT BULK ACTIONS
# =========================================================

@admin.action(description="Mark selected projects as planning")
def mark_projects_planning(modeladmin, request, queryset):
    queryset.update(
        status=Project.Status.PLANNING,
    )


@admin.action(description="Mark selected projects as active")
def mark_projects_active(modeladmin, request, queryset):
    queryset.update(
        status=Project.Status.ACTIVE,
    )


@admin.action(description="Mark selected projects as completed")
def mark_projects_completed(modeladmin, request, queryset):
    queryset.update(
        status=Project.Status.COMPLETED,
    )


@admin.action(description="Mark selected projects as cancelled")
def mark_projects_cancelled(modeladmin, request, queryset):
    queryset.update(
        status=Project.Status.CANCELLED,
    )


# =========================================================
# PROJECT ADMIN
# =========================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "problem",
        "selected_solution",
        "owner",
        "status",
        "start_date",
        "end_date",
        "progress_percentage",
        "created_at",
    )

    list_filter = (
        "status",
        "start_date",
        "end_date",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "problem__title",
        "selected_solution__title",
        "owner__username",
        "owner__email",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "progress_percentage",
        "created_at",
    )

    actions = (
        mark_projects_planning,
        mark_projects_active,
        mark_projects_completed,
        mark_projects_cancelled,
    )

    list_per_page = 25

    @admin.display(description="Progress")
    def progress_percentage(self, obj):
        return f"{obj.progress}%"