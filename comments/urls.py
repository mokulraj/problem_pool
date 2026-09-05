from django.urls import path

from . import views


app_name = "comments"


urlpatterns = [

    path(
        "comments/create/",
        views.comment_create,
        name="create",
    ),

    path(
        "comments/<int:pk>/edit/",
        views.comment_edit,
        name="edit",
    ),

    path(
        "comments/<int:pk>/delete/",
        views.comment_delete,
        name="delete",
    ),
]