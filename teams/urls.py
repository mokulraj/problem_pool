from django.urls import path

from . import views


app_name = "teams"


urlpatterns = [
    path(
        "projects/<int:project_id>/join/",
        views.join_project,
        name="join",
    ),

    path(
        "projects/<int:project_id>/join-requests/",
        views.project_join_requests,
        name="join_requests",
    ),

    path(
        "join-requests/<int:request_id>/approve/",
        views.approve_join_request,
        name="approve",
    ),

    path(
        "join-requests/<int:request_id>/reject/",
        views.reject_join_request,
        name="reject",
    ),

    path(
        "join-requests/<int:request_id>/cancel/",
        views.cancel_join_request,
        name="cancel",
    ),

    path(
        "projects/<int:project_id>/leave/",
        views.leave_project,
        name="leave",
    ),
]