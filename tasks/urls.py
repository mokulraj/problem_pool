from django.urls import path

from . import views


app_name = "tasks"


urlpatterns = [
    path(
        "projects/<int:project_id>/tasks/",
        views.task_list,
        name="list",
    ),

    path(
        "projects/<int:project_id>/tasks/create/",
        views.task_create,
        name="create",
    ),

    path(
        "tasks/<int:pk>/edit/",
        views.task_edit,
        name="edit",
    ),

    path(
        "tasks/<int:pk>/delete/",
        views.task_delete,
        name="delete",
    ),

    path(
        "tasks/<int:pk>/status/",
        views.task_status_update,
        name="status_update",
    ),

    path(
        "tasks/<int:pk>/complete/",
        views.task_complete,
        name="complete",
    ),
]