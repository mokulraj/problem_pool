from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from solutions.models import Solution

from .forms import ProjectForm
from .models import Project


@login_required
def project_list(request):
    projects = (
        Project.objects
        .select_related(
            "owner",
            "problem",
            "selected_solution",
        )
        .all()
    )

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
        },
    )


@login_required
def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related(
            "owner",
            "problem",
            "selected_solution",
            "selected_solution__proposed_by",
        ),
        pk=pk,
    )

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
        },
    )


@login_required
def project_create(request, solution_id):
    solution = get_object_or_404(
        Solution.objects.select_related(
            "problem",
            "problem__created_by",
        ),
        pk=solution_id,
    )

    problem = solution.problem

    # Only the problem creator can convert
    # the selected solution into a project.
    if problem.created_by != request.user:
        messages.error(
            request,
            "Only the problem owner can create this project.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if solution.status != Solution.Status.SELECTED:
        messages.error(
            request,
            "Only a selected solution can be converted into a project.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if hasattr(problem, "project"):
        messages.info(
            request,
            "A project already exists for this problem.",
        )

        return redirect(
            "projects:detail",
            pk=problem.project.pk,
        )

    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                project = form.save(commit=False)

                project.problem = problem
                project.selected_solution = solution
                project.owner = request.user

                project.save()

            messages.success(
                request,
                "Project created successfully.",
            )

            return redirect(
                "projects:detail",
                pk=project.pk,
            )

    else:
        form = ProjectForm(
            initial={
                "name": solution.title,
                "description": solution.description,
                "status": Project.Status.PLANNING,
            }
        )

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "solution": solution,
            "problem": problem,
            "page_title": "Convert Solution to Project",
        },
    )


@login_required
def project_edit(request, pk):
    project = get_object_or_404(
        Project.objects.select_related(
            "owner",
            "problem",
            "selected_solution",
        ),
        pk=pk,
    )

    if project.owner != request.user:
        messages.error(
            request,
            "You do not have permission to edit this project.",
        )

        return redirect(
            "projects:detail",
            pk=project.pk,
        )

    if request.method == "POST":
        form = ProjectForm(
            request.POST,
            instance=project,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Project updated successfully.",
            )

            return redirect(
                "projects:detail",
                pk=project.pk,
            )

    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "project": project,
            "page_title": "Edit Project",
        },
    )