from django.contrib import admin

from .models import JoinRequest, TeamMembership


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

    readonly_fields = (
        "joined_at",
    )


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
    )

    search_fields = (
        "project__name",
        "user__username",
        "user__email",
        "message",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )