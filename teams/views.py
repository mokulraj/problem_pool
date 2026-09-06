from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from notifications.models import Notification
from projects.models import Project

from .forms import JoinRequestForm
from .models import JoinRequest, TeamMembership


# =========================================================
# HELPERS
# =========================================================

def user_is_project_owner(user, project):
    return project.owner_id == user.id


def user_is_project_member(user, project):
    if project.owner_id == user.id:
        return True

    return TeamMembership.objects.filter(
        project=project,
        user=user,
    ).exists()


def get_valid_roles():
    return {
        value
        for value, label in TeamMembership.Role.choices
    }


# =========================================================
# JOIN PROJECT
# =========================================================

@login_required
def join_project(request, project_id):

    project = get_object_or_404(
        Project.objects.select_related("owner"),
        pk=project_id,
    )

    # Owner is automatically part of the project.
    if user_is_project_owner(request.user, project):

        messages.info(
            request,
            "You are already the owner of this project.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    # Already a member.
    if TeamMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists():

        messages.info(
            request,
            "You are already a member of this project.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    # Existing pending request.
    existing_request = JoinRequest.objects.filter(
        project=project,
        user=request.user,
        status=JoinRequest.Status.PENDING,
    ).first()

    if existing_request:

        messages.info(
            request,
            "You already have a pending join request.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if request.method == "POST":

        form = JoinRequestForm(request.POST)

        if form.is_valid():

            join_request = form.save(commit=False)

            join_request.project = project
            join_request.user = request.user

            try:
                join_request.full_clean()

            except ValidationError as exc:
                form.add_error(None, exc)

            else:

                with transaction.atomic():

                    join_request.save()

                    notification_message = (
                        f"{request.user.get_full_name() or request.user.username} "
                        f"requested to join your project: {project}"
                    )

                    notification_exists = (
                        Notification.objects.filter(
                            recipient=project.owner,
                            notification_type=(
                                Notification.NotificationType.JOIN_REQUEST
                            ),
                            related_project=project,
                            message=notification_message,
                        ).exists()
                    )

                    if not notification_exists:

                        Notification.objects.create(
                            recipient=project.owner,
                            message=notification_message,
                            notification_type=(
                                Notification.NotificationType.JOIN_REQUEST
                            ),
                            related_project=project,
                        )

                messages.success(
                    request,
                    "Your join request has been submitted.",
                )

                return redirect(
                    "projects:detail",
                    pk=project.pk,
                )

    else:

        form = JoinRequestForm()

    return render(
        request,
        "teams/join_request_form.html",
        {
            "form": form,
            "project": project,
        },
    )


# =========================================================
# CANCEL JOIN REQUEST
# =========================================================

@login_required
def cancel_join_request(request, request_id):

    join_request = get_object_or_404(
        JoinRequest.objects.select_related(
            "project",
            "user",
        ),
        pk=request_id,
    )

    project = join_request.project

    if join_request.user != request.user:

        messages.error(
            request,
            "You do not have permission to cancel this request.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if join_request.status != JoinRequest.Status.PENDING:

        messages.error(
            request,
            "Only pending requests can be cancelled.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    join_request.delete()

    messages.success(
        request,
        "Your join request has been cancelled.",
    )

    return redirect(
        "projects:detail",
        pk=project.pk,
    )


# =========================================================
# JOIN REQUEST LIST
# =========================================================

@login_required
def project_join_requests(request, project_id):

    project = get_object_or_404(
        Project.objects.select_related("owner"),
        pk=project_id,
    )

    if not user_is_project_owner(request.user, project):

        messages.error(
            request,
            "Only the project owner can manage join requests.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    join_requests = (
        JoinRequest.objects
        .filter(project=project)
        .select_related("user")
    )

    memberships = (
        TeamMembership.objects
        .filter(project=project)
        .select_related("user")
    )

    return render(
        request,
        "teams/join_requests.html",
        {
            "project": project,
            "join_requests": join_requests,
            "memberships": memberships,
            "role_choices": TeamMembership.Role.choices,
        },
    )


# =========================================================
# APPROVE JOIN REQUEST
# =========================================================

@login_required
def approve_join_request(request, request_id):

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "projects:list",
        )

    join_request = get_object_or_404(
        JoinRequest.objects.select_related(
            "project",
            "user",
        ),
        pk=request_id,
    )

    project = join_request.project

    if not user_is_project_owner(request.user, project):

        messages.error(
            request,
            "Only the project owner can approve join requests.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if join_request.status != JoinRequest.Status.PENDING:

        messages.error(
            request,
            "This request is no longer pending.",
        )

        return redirect(
            "teams:join_requests",
            project_id=project.pk,
        )

    selected_role = request.POST.get(
        "role",
        TeamMembership.Role.OTHER,
    )

    if selected_role not in get_valid_roles():

        messages.error(
            request,
            "Invalid team role.",
        )

        return redirect(
            "teams:join_requests",
            project_id=project.pk,
        )

    with transaction.atomic():

        membership, created = TeamMembership.objects.get_or_create(
            project=project,
            user=join_request.user,
            defaults={
                "role": selected_role,
            },
        )

        if not created:

            membership.role = selected_role

            membership.save(
                update_fields=["role"],
            )

        join_request.status = JoinRequest.Status.APPROVED

        join_request.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        Notification.objects.create(
            recipient=join_request.user,
            message=(
                f"Your request to join '{project}' was approved. "
                f"Your role is {membership.get_role_display()}."
            ),
            notification_type=(
                Notification.NotificationType.JOIN_APPROVED
            ),
            related_project=project,
        )

    messages.success(
        request,
        (
            f"{join_request.user.username} has joined the project "
            f"as {membership.get_role_display()}."
        ),
    )

    return redirect(
        "teams:join_requests",
        project_id=project.pk,
    )


# =========================================================
# REJECT JOIN REQUEST
# =========================================================

@login_required
def reject_join_request(request, request_id):

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "projects:list",
        )

    join_request = get_object_or_404(
        JoinRequest.objects.select_related(
            "project",
            "user",
        ),
        pk=request_id,
    )

    project = join_request.project

    if not user_is_project_owner(request.user, project):

        messages.error(
            request,
            "Only the project owner can reject join requests.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if join_request.status != JoinRequest.Status.PENDING:

        messages.error(
            request,
            "This request is no longer pending.",
        )

        return redirect(
            "teams:join_requests",
            project_id=project.pk,
        )

    join_request.status = JoinRequest.Status.REJECTED

    join_request.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    messages.success(
        request,
        "Join request rejected.",
    )

    return redirect(
        "teams:join_requests",
        project_id=project.pk,
    )


# =========================================================
# CHANGE MEMBER ROLE
# =========================================================

@login_required
def change_member_role(request, project_id, user_id):

    project = get_object_or_404(
        Project.objects.select_related("owner"),
        pk=project_id,
    )

    if not user_is_project_owner(request.user, project):

        messages.error(
            request,
            "Only the project owner can change member roles.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "teams:join_requests",
            project_id=project.pk,
        )

    membership = get_object_or_404(
        TeamMembership.objects.select_related("user"),
        project=project,
        user_id=user_id,
    )

    new_role = request.POST.get("role")

    if new_role not in get_valid_roles():

        messages.error(
            request,
            "Invalid team role.",
        )

        return redirect(
            "teams:join_requests",
            project_id=project.pk,
        )

    old_role = membership.get_role_display()

    membership.role = new_role

    membership.save(
        update_fields=["role"],
    )

    new_role_display = membership.get_role_display()

    Notification.objects.create(
        recipient=membership.user,
        message=(
            f"Your role in '{project}' was changed from "
            f"{old_role} to {new_role_display}."
        ),
        notification_type=(
            Notification.NotificationType.JOIN_APPROVED
        ),
        related_project=project,
    )

    messages.success(
        request,
        (
            f"{membership.user.username}'s role changed to "
            f"{new_role_display}."
        ),
    )

    return redirect(
        "teams:join_requests",
        project_id=project.pk,
    )


# =========================================================
# REMOVE MEMBER
# =========================================================

@login_required
def remove_member(request, project_id, user_id):

    project = get_object_or_404(
        Project.objects.select_related("owner"),
        pk=project_id,
    )

    if not user_is_project_owner(request.user, project):

        messages.error(
            request,
            "Only the project owner can remove members.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "teams:join_requests",
            project_id=project.pk,
        )

    membership = get_object_or_404(
        TeamMembership.objects.select_related("user"),
        project=project,
        user_id=user_id,
    )

    member = membership.user

    membership.delete()

    Notification.objects.create(
        recipient=member,
        message=(
            f"You have been removed from the project '{project}'."
        ),
        notification_type=(
            Notification.NotificationType.JOIN_REQUEST
        ),
        related_project=project,
    )

    messages.success(
        request,
        f"{member.username} has been removed from the project.",
    )

    return redirect(
        "teams:join_requests",
        project_id=project.pk,
    )


# =========================================================
# LEAVE PROJECT
# =========================================================

@login_required
def leave_project(request, project_id):

    project = get_object_or_404(
        Project,
        pk=project_id,
    )

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if user_is_project_owner(request.user, project):

        messages.error(
            request,
            "The project owner cannot leave their own project.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    membership = TeamMembership.objects.filter(
        project=project,
        user=request.user,
    ).first()

    if membership is None:

        messages.error(
            request,
            "You are not a member of this project.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    membership.delete()

    messages.success(
        request,
        "You have left the project.",
    )

    return redirect(
        "projects:detail",
        pk=project.pk,
    )