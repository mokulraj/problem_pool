from django.urls import path

from . import views


app_name = "problems"


urlpatterns = [

    path(
        "problems/",
        views.problem_list,
        name="list",
    ),

    path(
        "problems/create/",
        views.problem_create,
        name="create",
    ),

    path(
        "problems/<int:pk>/",
        views.problem_detail,
        name="detail",
    ),

    path(
        "problems/<int:pk>/edit/",
        views.problem_edit,
        name="edit",
    ),

    path(
        "problems/<int:pk>/delete/",
        views.problem_delete,
        name="delete",
    ),
]