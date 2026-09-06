from django.contrib import admin

from .models import ReputationReward


@admin.register(ReputationReward)
class ReputationRewardAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "reward_type",
        "points",
        "reference_id",
        "created_at",
    )

    list_filter = (
        "reward_type",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )