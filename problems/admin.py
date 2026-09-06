from django.contrib import admin

from .models import Problem


@admin.action(description="Mark selected problems as open")
def mark_problems_open(modeladmin, request, queryset):
    queryset.update(
        status=Problem.Status.OPEN,
    )


@admin.action(description="Mark selected problems as in progress")
def mark_problems_in_progress(modeladmin, request, queryset):
    queryset.update(
        status=Problem.Status.IN_PROGRESS,
    )


@admin.action(description="Mark selected problems as solved")
def mark_problems_solved(modeladmin, request, queryset):
    queryset.update(
        status=Problem.Status.SOLVED,
    )


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):

    # =========================================================
    # LIST DISPLAY
    # =========================================================

    list_display = (
        "title",
        "created_by",
        "category",
        "status",
        "priority",
        "views",
        "solution_count",
        "created_at",
        "updated_at",
    )

    # =========================================================
    # FILTERS
    # =========================================================

    list_filter = (
        "category",
        "status",
        "priority",
        "created_at",
        "updated_at",
    )

    # =========================================================
    # SEARCH
    # =========================================================

    search_fields = (
        "title",
        "description",
        "location",
        "created_by__username",
        "created_by__email",
    )

    # =========================================================
    # ORDERING
    # =========================================================

    ordering = (
        "-created_at",
    )

    # =========================================================
    # READ-ONLY AUDIT / STATISTICS
    # =========================================================

    readonly_fields = (
        "views",
        "solution_count",
        "created_at",
        "updated_at",
    )

    # =========================================================
    # BULK MODERATION ACTIONS
    # =========================================================

    actions = (
        mark_problems_open,
        mark_problems_in_progress,
        mark_problems_solved,
    )

    # =========================================================
    # ADMIN PAGINATION
    # =========================================================

    list_per_page = 25