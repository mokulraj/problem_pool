from django.contrib import admin

from .models import Comment


# =========================================================
# COMMENT MODERATION ACTION
# =========================================================

@admin.action(description="Delete selected comments")
def delete_selected_comments(modeladmin, request, queryset):
    queryset.delete()


# =========================================================
# COMMENT ADMIN
# =========================================================

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

    actions = (
        delete_selected_comments,
    )

    list_per_page = 25

    # =====================================================
    # DISPLAY HELPERS
    # =====================================================

    @admin.display(
        description="Target",
    )
    def target(self, obj):

        if obj.solution:
            return f"Solution: {obj.solution.title}"

        if obj.problem:
            return f"Problem: {obj.problem.title}"

        return "-"

    @admin.display(
        description="Comment",
    )
    def short_content(self, obj):

        if len(obj.content) > 70:
            return f"{obj.content[:70]}..."

        return obj.content