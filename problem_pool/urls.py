from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    # Public home page
    path(
        "",
        include("core.urls"),
    ),

    # Dashboard
    path(
        "",
        include("dashboard.urls"),
    ),

    # Accounts
    path(
        "",
        include("accounts.urls"),
    ),

    # Problems
    path(
        "",
        include("problems.urls"),
    ),

    # Solutions
    path(
        "",
        include("solutions.urls"),
    ),

    # Comments
    path(
        "",
        include("comments.urls"),
    ),

    # Projects
    path(
        "",
        include("projects.urls"),
    ),

    # Teams
    path(
        "",
        include("teams.urls"),
    ),

    # Tasks
    path(
        "",
        include("tasks.urls"),
    ),
]


# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )