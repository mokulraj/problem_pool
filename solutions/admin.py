from django.contrib import admin

from .models import Solution


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "problem",
        "proposed_by",
        "status",
        "upvotes",
        "downvotes",
        "score",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "problem__title",
        "proposed_by__username",
        "proposed_by__email",
    )

    ordering = (
        "-score",
        "-created_at",
    )

    readonly_fields = (
        "upvotes",
        "downvotes",
        "score",
        "created_at",
        "updated_at",
    )