from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project

from .forms import JoinRequestForm
from .models import JoinRequest, TeamMembership


@login_required
def join_project(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner"),
        pk=project_id,
    )

    if project.owner == request.user:
        messages.info(
            request,
            "You are already the owner of this project.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

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
            except Exception as exc:
                form.add_error(
                    None,
                    exc,
                )
            else:
                join_request.save()

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


@login_required
def cancel_join_request(request, request_id):
    join_request = get_object_or_404(
        JoinRequest.objects.select_related(
            "project",
            "user",
        ),
        pk=request_id,
    )

    if join_request.user != request.user:
        messages.error(
            request,
            "You do not have permission to cancel this request.",
        )

        return redirect(
            "projects:detail",
            pk=join_request.project.pk,
        )

    if join_request.status != JoinRequest.Status.PENDING:
        messages.error(
            request,
            "Only pending requests can be cancelled.",
        )

        return redirect(
            "projects:detail",
            pk=join_request.project.pk,
        )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "projects:detail",
            pk=join_request.project.pk,
        )

    project_id = join_request.project.pk

    join_request.delete()

    messages.success(
        request,
        "Your join request has been cancelled.",
    )

    return redirect(
        "projects:detail",
        pk=project_id,
    )


@login_required
def project_join_requests(request, project_id):
    project = get_object_or_404(
        Project,
        pk=project_id,
    )

    if project.owner != request.user:
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
        .filter(
            project=project,
        )
        .select_related("user")
    )

    return render(
        request,
        "teams/join_requests.html",
        {
            "project": project,
            "join_requests": join_requests,
        },
    )


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

    if project.owner != request.user:
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

    with transaction.atomic():
        membership, created = TeamMembership.objects.get_or_create(
            project=project,
            user=join_request.user,
            defaults={
                "role": TeamMembership.Role.MEMBER,
            },
        )

        if not created:
            messages.info(
                request,
                "This user is already a team member.",
            )

            join_request.status = JoinRequest.Status.APPROVED
            join_request.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return redirect(
                "teams:join_requests",
                project_id=project.pk,
            )

        join_request.status = JoinRequest.Status.APPROVED

        join_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    messages.success(
        request,
        f"{join_request.user.username} has joined the project.",
    )

    return redirect(
        "teams:join_requests",
        project_id=project.pk,
    )


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

    if project.owner != request.user:
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
        ]
    )

    messages.success(
        request,
        "Join request rejected.",
    )

    return redirect(
        "teams:join_requests",
        project_id=project.pk,
    )


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

    if project.owner == request.user:
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