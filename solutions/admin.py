from django.contrib import admin

from .models import Solution, Vote


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


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "solution",
        "vote_type",
        "created_at",
    )

    list_filter = (
        "vote_type",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "solution__title",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )