from django.urls import path

from . import views


app_name = "projects"


urlpatterns = [
    path(
        "projects/",
        views.project_list,
        name="list",
    ),
    path(
        "projects/create/<int:solution_id>/",
        views.project_create,
        name="create",
    ),
    path(
        "projects/<int:pk>/",
        views.project_detail,
        name="detail",
    ),
    path(
        "projects/<int:pk>/edit/",
        views.project_edit,
        name="edit",
    ),
]