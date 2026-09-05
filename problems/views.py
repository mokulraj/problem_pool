from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProblemForm
from .models import Problem
from solutions.models import Solution


def problem_list(request):

    problems = Problem.objects.select_related(
        "created_by"
    )

    search_query = request.GET.get(
        "q",
        ""
    ).strip()

    category = request.GET.get(
        "category",
        ""
    )

    status = request.GET.get(
        "status",
        ""
    )

    priority = request.GET.get(
        "priority",
        ""
    )

    sort = request.GET.get(
        "sort",
        "newest"
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search_query:

        problems = problems.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__icontains=search_query)
            | Q(location__icontains=search_query)
        )


    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    if category:
        problems = problems.filter(
            category=category
        )

    if status:
        problems = problems.filter(
            status=status
        )

    if priority:
        problems = problems.filter(
            priority=priority
        )


    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    if sort == "most_viewed":

        problems = problems.order_by(
            "-views",
            "-created_at"
        )

    elif sort == "most_solutions":

        problems = problems.order_by(
            "-solution_count",
            "-created_at"
        )

    else:

        problems = problems.order_by(
            "-created_at"
        )


    context = {
        "problems": problems,
        "categories": Problem.Category.choices,
        "statuses": Problem.Status.choices,
        "priorities": Problem.Priority.choices,

        "search_query": search_query,
        "selected_category": category,
        "selected_status": status,
        "selected_priority": priority,
        "selected_sort": sort,
    }

    return render(
        request,
        "problems/problem_list.html",
        context
    )


def problem_detail(request, pk):
    
    problem = get_object_or_404(
        Problem.objects.select_related(
            "created_by"
        ),
        pk=pk,
    )

    solutions = (
        Solution.objects
        .filter(problem=problem)
        .select_related("proposed_by")
        .order_by("-score", "-created_at")
    )


    Problem.objects.filter(
        pk=problem.pk
    ).update(
        views=problem.views + 1
    )

    problem.views += 1


    return render(
        request,
        "problems/problem_detail.html",
        {
            "problem": problem,
            "solutions": solutions,
        }
    )

    if request.user != problem.created_by:
        Problem.objects.filter(
            pk=problem.pk
        ).update(
            views=problem.views + 1
        )

        problem.views += 1

    return render(
        request,
        "problems/problem_detail.html",
        {
            "problem": problem,
        }
    )

@login_required
def problem_create(request):

    if request.method == "POST":

        form = ProblemForm(request.POST)

        if form.is_valid():

            problem = form.save(
                commit=False
            )

            problem.created_by = request.user

            problem.save()

            messages.success(
                request,
                "Problem created successfully."
            )

            return redirect(
                "problems:detail",
                pk=problem.pk
            )

    else:

        form = ProblemForm()


    return render(
        request,
        "problems/problem_form.html",
        {
            "form": form,
            "page_title": "Post a Problem",
            "submit_text": "Create Problem",
        }
    )


@login_required
def problem_edit(request, pk):

    problem = get_object_or_404(
        Problem,
        pk=pk
    )


    if problem.created_by != request.user:

        messages.error(
            request,
            "You do not have permission to edit this problem."
        )

        return redirect(
            "problems:detail",
            pk=problem.pk
        )


    if request.method == "POST":

        form = ProblemForm(
            request.POST,
            instance=problem
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Problem updated successfully."
            )

            return redirect(
                "problems:detail",
                pk=problem.pk
            )

    else:

        form = ProblemForm(
            instance=problem
        )


    return render(
        request,
        "problems/problem_form.html",
        {
            "form": form,
            "problem": problem,
            "page_title": "Edit Problem",
            "submit_text": "Save Changes",
        }
    )


@login_required
def problem_delete(request, pk):

    problem = get_object_or_404(
        Problem,
        pk=pk
    )


    if problem.created_by != request.user:

        messages.error(
            request,
            "You do not have permission to delete this problem."
        )

        return redirect(
            "problems:detail",
            pk=problem.pk
        )


    if request.method == "POST":

        problem.delete()

        messages.success(
            request,
            "Problem deleted successfully."
        )

        return redirect(
            "problems:list"
        )


    return render(
        request,
        "problems/problem_confirm_delete.html",
        {
            "problem": problem,
        }
    )