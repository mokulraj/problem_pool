from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from notifications.models import Notification
from projects.models import Project
from reputation.services import award_points
from teams.models import TeamMembership

from .forms import TaskForm
from .models import Task


def user_is_project_member(user, project):
    if project.owner_id == user.id:
        return True

    return TeamMembership.objects.filter(
        project=project,
        user=user,
    ).exists()


def user_is_project_owner(user, project):
    return project.owner_id == user.id


@login_required
def task_list(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner"),
        pk=project_id,
    )

    if not user_is_project_member(request.user, project):
        return HttpResponseForbidden(
            "You must be a member of the project to view its tasks."
        )

    tasks = (
        Task.objects
        .filter(project=project)
        .select_related("assigned_to")
    )

    return render(
        request,
        "tasks/task_list.html",
        {
            "project": project,
            "tasks": tasks,
        },
    )


@login_required
def task_create(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner"),
        pk=project_id,
    )

    if not user_is_project_owner(request.user, project):
        return HttpResponseForbidden(
            "Only the project owner can create tasks."
        )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            project=project,
        )

        if form.is_valid():
            task = form.save(commit=False)

            task.project = project
            task.status = Task.Status.TODO

            task.full_clean()
            task.save()

            if task.assigned_to:
                Notification.objects.create(
                    recipient=task.assigned_to,
                    message=(
                        f"You have been assigned the task "
                        f"'{task.title}' in project "
                        f"'{project}'."
                    ),
                    notification_type=(
                        Notification.NotificationType.TASK_ASSIGNED
                    ),
                    related_project=project,
                )

            messages.success(
                request,
                "Task created successfully.",
            )

            return redirect(
                "tasks:list",
                project_id=project.pk,
            )

    else:
        form = TaskForm(
            project=project,
        )

    return render(
        request,
        "tasks/task_form.html",
        {
            "form": form,
            "project": project,
            "page_title": "Create Task",
        },
    )


@login_required
def task_edit(request, pk):
    task = get_object_or_404(
        Task.objects.select_related(
            "project",
            "assigned_to",
        ),
        pk=pk,
    )

    project = task.project

    if not user_is_project_owner(request.user, project):
        return HttpResponseForbidden(
            "Only the project owner can edit tasks."
        )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
            project=project,
        )

        if form.is_valid():
            old_assigned_to = task.assigned_to
            current_status = task.status

            task = form.save(commit=False)

            task.status = current_status

            task.full_clean()
            task.save()

            if (
                task.assigned_to
                and task.assigned_to != old_assigned_to
            ):
                Notification.objects.create(
                    recipient=task.assigned_to,
                    message=(
                        f"You have been assigned the task "
                        f"'{task.title}' in project "
                        f"'{project}'."
                    ),
                    notification_type=(
                        Notification.NotificationType.TASK_ASSIGNED
                    ),
                    related_project=project,
                )

            messages.success(
                request,
                "Task updated successfully.",
            )

            return redirect(
                "tasks:list",
                project_id=project.pk,
            )

    else:
        form = TaskForm(
            instance=task,
            project=project,
        )

    return render(
        request,
        "tasks/task_form.html",
        {
            "form": form,
            "project": project,
            "task": task,
            "page_title": "Edit Task",
        },
    )


@login_required
def task_delete(request, pk):
    task = get_object_or_404(
        Task.objects.select_related("project"),
        pk=pk,
    )

    project = task.project

    if not user_is_project_owner(request.user, project):
        return HttpResponseForbidden(
            "Only the project owner can delete tasks."
        )

    if request.method != "POST":
        return HttpResponseForbidden(
            "Task deletion requires a POST request."
        )

    task.delete()

    messages.success(
        request,
        "Task deleted successfully.",
    )

    return redirect(
        "tasks:list",
        project_id=project.pk,
    )


@login_required
def task_status_update(request, pk):
    """
    Only the member assigned to the task can change its status.

    The project owner can view the status but cannot change it.
    """

    task = get_object_or_404(
        Task.objects.select_related(
            "project",
            "project__owner",
            "assigned_to",
        ),
        pk=pk,
    )

    project = task.project

    if task.assigned_to != request.user:
        return HttpResponseForbidden(
            "Only the member assigned to this task can update its status."
        )

    if request.method != "POST":
        return HttpResponseForbidden(
            "Task status updates require a POST request."
        )

    new_status = request.POST.get("status")

    valid_statuses = {
        Task.Status.TODO,
        Task.Status.IN_PROGRESS,
        Task.Status.COMPLETED,
    }

    if new_status not in valid_statuses:
        messages.error(
            request,
            "Invalid task status.",
        )

        return redirect(
            "tasks:list",
            project_id=project.pk,
        )

    old_status = task.status

    if old_status == new_status:
        messages.info(
            request,
            "The task is already in that status.",
        )

        return redirect(
            "tasks:list",
            project_id=project.pk,
        )

    task.status = new_status

    task.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    if (
        new_status == Task.Status.COMPLETED
        and old_status != Task.Status.COMPLETED
    ):
        award_points(
            request.user,
            "TASK_COMPLETED",
            task.pk,
        )

    if project.owner_id != request.user.id:

        Notification.objects.create(
            recipient=project.owner,
            message=(
                f"{request.user.username} updated the task "
                f"'{task.title}' from "
                f"'{dict(Task.Status.choices).get(old_status)}' "
                f"to "
                f"'{task.get_status_display()}'."
            ),
            notification_type=(
                Notification.NotificationType.TASK_ASSIGNED
            ),
            related_project=project,
        )

    messages.success(
        request,
        f"Task status updated to {task.get_status_display()}.",
    )

    return redirect(
        "tasks:list",
        project_id=project.pk,
    )


@login_required
def task_complete(request, pk):
    """
    Kept for backwards compatibility.

    The task list UI no longer uses this endpoint.
    """

    task = get_object_or_404(
        Task.objects.select_related("project"),
        pk=pk,
    )

    project = task.project

    if task.assigned_to != request.user:
        return HttpResponseForbidden(
            "Only the assigned member can complete this task."
        )

    if request.method != "POST":
        return HttpResponseForbidden(
            "Task completion requires a POST request."
        )

    old_status = task.status

    if old_status == Task.Status.COMPLETED:
        messages.info(
            request,
            "This task is already completed.",
        )

        return redirect(
            "tasks:list",
            project_id=project.pk,
        )

    task.status = Task.Status.COMPLETED

    task.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    award_points(
        request.user,
        "TASK_COMPLETED",
        task.pk,
    )

    Notification.objects.create(
        recipient=project.owner,
        message=(
            f"{request.user.username} completed the task "
            f"'{task.title}'."
        ),
        notification_type=(
            Notification.NotificationType.TASK_ASSIGNED
        ),
        related_project=project,
    )

    messages.success(
        request,
        "Task marked as completed. You earned 5 reputation points!",
    )

    return redirect(
        "tasks:list",
        project_id=project.pk,
    )