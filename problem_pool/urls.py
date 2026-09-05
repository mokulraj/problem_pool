from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "",
        include("core.urls"),
    ),

    path(
        "",
        include("accounts.urls"),
    ),

    path(
        "",
        include("problems.urls"),
    ),

    path(
        "",
        include("solutions.urls"),
    ),

    path(
        "",
        include("comments.urls"),
    ),

    path(
        "",
        include("projects.urls"),
    ),

    path(
        "",
        include("teams.urls"),
    ),

    path(
        "",
        include("tasks.urls"),
    ),
]