from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project
from teams.models import TeamMembership

from .forms import TaskForm
from .models import Task


def user_can_manage_project(user, project):
    if project.owner == user:
        return True

    return TeamMembership.objects.filter(
        project=project,
        user=user,
    ).exists()


@login_required
def task_list(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related(
            "owner",
        ),
        pk=project_id,
    )

    if not user_can_manage_project(
        request.user,
        project,
    ):
        messages.error(
            request,
            "You must be part of the project to view its tasks.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
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
        Project,
        pk=project_id,
    )

    if not user_can_manage_project(
        request.user,
        project,
    ):
        messages.error(
            request,
            "Only project members can create tasks.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            project=project,
        )

        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.full_clean()
            task.save()

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
        ),
        pk=pk,
    )

    project = task.project

    if not user_can_manage_project(
        request.user,
        project,
    ):
        messages.error(
            request,
            "Only project members can edit tasks.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
            project=project,
        )

        if form.is_valid():
            task = form.save(commit=False)
            task.full_clean()
            task.save()

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
        Task.objects.select_related(
            "project",
        ),
        pk=pk,
    )

    project = task.project

    if project.owner != request.user:
        messages.error(
            request,
            "Only the project owner can delete tasks.",
        )

        return redirect(
            "tasks:list",
            project_id=project.pk,
        )

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "tasks:list",
            project_id=project.pk,
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
def task_complete(request, pk):
    task = get_object_or_404(
        Task.objects.select_related(
            "project",
        ),
        pk=pk,
    )

    project = task.project

    if not user_can_manage_project(
        request.user,
        project,
    ):
        messages.error(
            request,
            "Only project members can update tasks.",
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
            "tasks:list",
            project_id=project.pk,
        )

    task.status = Task.Status.COMPLETED
    task.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Task marked as completed.",
    )

    return redirect(
        "tasks:list",
        project_id=project.pk,
    )