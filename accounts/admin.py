from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "points",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    ordering = (
        "-date_joined",
    )

    fieldsets = UserAdmin.fieldsets + (
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
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "ProblemPool Profile",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                )
            },
        ),
    )