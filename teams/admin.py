from django.contrib import admin

from .models import JoinRequest, TeamMembership


# =========================================================
# TEAM MEMBERSHIP ACTIONS
# =========================================================

@admin.action(description="Remove selected team memberships")
def remove_selected_memberships(modeladmin, request, queryset):
    queryset.delete()


# =========================================================
# JOIN REQUEST ACTIONS
# =========================================================

@admin.action(description="Approve selected join requests")
def approve_join_requests(modeladmin, request, queryset):
    queryset.update(
        status=JoinRequest.Status.APPROVED,
    )


@admin.action(description="Reject selected join requests")
def reject_join_requests(modeladmin, request, queryset):
    queryset.update(
        status=JoinRequest.Status.REJECTED,
    )


@admin.action(description="Reset selected join requests to pending")
def reset_join_requests(modeladmin, request, queryset):
    queryset.update(
        status=JoinRequest.Status.PENDING,
    )


# =========================================================
# TEAM MEMBERSHIP ADMIN
# =========================================================

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):

    list_display = (
        "project",
        "user",
        "role",
        "joined_at",
    )

    list_filter = (
        "role",
        "joined_at",
    )

    search_fields = (
        "project__name",
        "user__username",
        "user__email",
    )

    ordering = (
        "-joined_at",
    )

    readonly_fields = (
        "joined_at",
    )

    actions = (
        remove_selected_memberships,
    )

    list_per_page = 25


# =========================================================
# JOIN REQUEST ADMIN
# =========================================================

@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):

    list_display = (
        "project",
        "user",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "project__name",
        "user__username",
        "user__email",
        "message",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    actions = (
        approve_join_requests,
        reject_join_requests,
        reset_join_requests,
    )

    list_per_page = 25