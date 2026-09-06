from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    # =========================================================
    # LIST DISPLAY
    # =========================================================

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "points",
        "level",
        "is_active",
        "is_staff",
        "date_joined",
    )

    # =========================================================
    # FILTERS
    # =========================================================

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )

    # =========================================================
    # SEARCH
    # =========================================================

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "location",
        "skills",
    )

    # =========================================================
    # ORDERING
    # =========================================================

    ordering = (
        "-date_joined",
    )

    # =========================================================
    # READ-ONLY AUDIT FIELDS
    # =========================================================

    readonly_fields = (
        "date_joined",
        "last_login",
    )

    # =========================================================
    # EDIT USER
    # =========================================================

    fieldsets = (
        (
            "Authentication",
            {
                "fields": (
                    "username",
                    "password",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )
            },
        ),
        (
            "ProblemPool Profile",
            {
                "fields": (
                    "profile_image",
                    "bio",
                    "location",
                    "skills",
                    "points",
                    "role",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    # =========================================================
    # ADD USER
    # =========================================================

    add_fieldsets = (
        (
            None,
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )
            },
        ),
        (
            "ProblemPool Profile",
            {
                "fields": (
                    "role",
                )
            },
        ),
    )

    # =========================================================
    # PERFORMANCE
    # =========================================================

    list_per_page = 25