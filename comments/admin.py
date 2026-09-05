from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "target",
        "short_content",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "content",
        "user__username",
        "user__email",
        "problem__title",
        "solution__title",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def target(self, obj):

        if obj.solution:
            return f"Solution: {obj.solution.title}"

        if obj.problem:
            return f"Problem: {obj.problem.title}"

        return "-"

    target.short_description = "Target"

    def short_content(self, obj):

        return obj.content[:70]

    short_content.short_description = "Comment"