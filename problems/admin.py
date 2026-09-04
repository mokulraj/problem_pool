from django.contrib import admin

from .models import Problem


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "created_by",
        "category",
        "status",
        "priority",
        "views",
        "solution_count",
        "created_at",
    )

    list_filter = (
        "category",
        "status",
        "priority",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "location",
        "created_by__username",
        "created_by__email",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "views",
        "solution_count",
        "created_at",
        "updated_at",
    )