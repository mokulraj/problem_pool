from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from problems.models import Problem

from .forms import SolutionForm
from .models import Solution


def solution_detail(request, pk):

    solution = get_object_or_404(
        Solution.objects.select_related(
            "problem",
            "proposed_by",
        ),
        pk=pk,
    )

    return render(
        request,
        "solutions/solution_detail.html",
        {
            "solution": solution,
        },
    )


@login_required
def solution_create(request):

    problem_id = request.GET.get("problem")

    if not problem_id:
        messages.error(
            request,
            "A problem is required before submitting a solution.",
        )

        return redirect(
            "problems:list"
        )

    problem = get_object_or_404(
        Problem,
        pk=problem_id,
    )

    if problem.status in [
        Problem.Status.SOLVED,
        Problem.Status.CLOSED,
    ]:
        messages.warning(
            request,
            "Solutions cannot be submitted to a closed or solved problem.",
        )

        return redirect(
            "problems:detail",
            pk=problem.pk,
        )

    if request.method == "POST":

        form = SolutionForm(
            request.POST
        )

        if form.is_valid():

            with transaction.atomic():

                solution = form.save(
                    commit=False
                )

                solution.problem = problem
                solution.proposed_by = request.user

                solution.save()

                Problem.objects.filter(
                    pk=problem.pk
                ).update(
                    solution_count=problem.solution_count + 1
                )

            messages.success(
                request,
                "Solution submitted successfully.",
            )

            return redirect(
                "solutions:detail",
                pk=solution.pk,
            )

    else:

        form = SolutionForm()


    return render(
        request,
        "solutions/solution_form.html",
        {
            "form": form,
            "problem": problem,
            "page_title": "Propose a Solution",
            "submit_text": "Submit Solution",
        },
    )


@login_required
def solution_edit(request, pk):

    solution = get_object_or_404(
        Solution,
        pk=pk,
    )

    if solution.proposed_by != request.user:

        messages.error(
            request,
            "You do not have permission to edit this solution.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if solution.status == Solution.Status.SELECTED:

        messages.warning(
            request,
            "A selected solution cannot be edited.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if request.method == "POST":

        form = SolutionForm(
            request.POST,
            instance=solution,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Solution updated successfully.",
            )

            return redirect(
                "solutions:detail",
                pk=solution.pk,
            )

    else:

        form = SolutionForm(
            instance=solution,
        )


    return render(
        request,
        "solutions/solution_form.html",
        {
            "form": form,
            "problem": solution.problem,
            "solution": solution,
            "page_title": "Edit Solution",
            "submit_text": "Save Changes",
        },
    )


@login_required
def solution_delete(request, pk):

    solution = get_object_or_404(
        Solution,
        pk=pk,
    )

    if solution.proposed_by != request.user:

        messages.error(
            request,
            "You do not have permission to delete this solution.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if solution.status == Solution.Status.SELECTED:

        messages.warning(
            request,
            "A selected solution cannot be deleted.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if request.method == "POST":

        problem_id = solution.problem_id

        solution.delete()

        Problem.objects.filter(
            pk=problem_id,
            solution_count__gt=0,
        ).update(
            solution_count=F("solution_count") - 1
        )

        messages.success(
            request,
            "Solution deleted successfully.",
        )

        return redirect(
            "problems:detail",
            pk=problem_id,
        )


    return render(
        request,
        "solutions/solution_confirm_delete.html",
        {
            "solution": solution,
        },
    )