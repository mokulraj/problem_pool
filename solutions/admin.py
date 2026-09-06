from django.contrib import admin

from .models import Solution, Vote


# =========================================================
# SOLUTION BULK ACTIONS
# =========================================================

@admin.action(description="Mark selected solutions as proposed")
def mark_solutions_proposed(modeladmin, request, queryset):
    queryset.update(
        status=Solution.Status.PROPOSED,
    )


@admin.action(description="Shortlist selected solutions")
def mark_solutions_shortlisted(modeladmin, request, queryset):
    queryset.update(
        status=Solution.Status.SHORTLISTED,
    )


@admin.action(description="Select selected solutions")
def mark_solutions_selected(modeladmin, request, queryset):
    queryset.update(
        status=Solution.Status.SELECTED,
    )


@admin.action(description="Reject selected solutions")
def mark_solutions_rejected(modeladmin, request, queryset):
    queryset.update(
        status=Solution.Status.REJECTED,
    )


# =========================================================
# SOLUTION ADMIN
# =========================================================

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
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
        "updated_at",
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

    actions = (
        mark_solutions_proposed,
        mark_solutions_shortlisted,
        mark_solutions_selected,
        mark_solutions_rejected,
    )

    list_per_page = 25


# =========================================================
# VOTE ADMIN
# =========================================================

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
        "solution__problem__title",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )

    list_per_page = 25