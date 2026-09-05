from django.urls import path

from . import views


app_name = "solutions"


urlpatterns = [

    path(
        "solutions/create/",
        views.solution_create,
        name="create",
    ),

    path(
        "solutions/<int:pk>/",
        views.solution_detail,
        name="detail",
    ),

    path(
        "solutions/<int:pk>/edit/",
        views.solution_edit,
        name="edit",
    ),

    path(
        "solutions/<int:pk>/delete/",
        views.solution_delete,
        name="delete",
    ),
    
    path(
    "solutions/<int:pk>/vote/",
    views.vote_solution,
    name="vote",
),
    
    path(
    "solutions/<int:pk>/select/",
    views.select_solution,
    name="select",
),
    
    path(
    "solutions/",
    views.solution_list,
    name="list",
),
]