from django.urls import path

from . import views


app_name = "teams"


urlpatterns = [
    # =========================================================
    # JOIN PROJECT
    # =========================================================

    path(
        "projects/<int:project_id>/join/",
        views.join_project,
        name="join",
    ),


    # =========================================================
    # JOIN REQUESTS
    # =========================================================

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


    # =========================================================
    # MEMBER MANAGEMENT
    # =========================================================

    path(
        "projects/<int:project_id>/members/<int:user_id>/role/",
        views.change_member_role,
        name="change_member_role",
    ),

    path(
        "projects/<int:project_id>/members/<int:user_id>/remove/",
        views.remove_member,
        name="remove_member",
    ),


    # =========================================================
    # LEAVE PROJECT
    # =========================================================

    path(
        "projects/<int:project_id>/leave/",
        views.leave_project,
        name="leave",
    ),
]