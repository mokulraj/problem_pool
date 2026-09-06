from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from problems.models import Problem
from projects.models import Project
from solutions.models import Solution


@login_required
def global_search(request):
    query = request.GET.get("q", "").strip()

    problems = Problem.objects.none()
    solutions = Solution.objects.none()
    projects = Project.objects.none()
    users = get_user_model().objects.none()

    if query:
        problems = (
            Problem.objects
            .filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(category__icontains=query)
                | Q(location__icontains=query)
                | Q(created_by__username__icontains=query)
            )
            .select_related("created_by")
            .order_by("-created_at")
        )

        solutions = (
            Solution.objects
            .filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(problem__title__icontains=query)
                | Q(proposed_by__username__icontains=query)
            )
            .select_related("problem", "proposed_by")
            .order_by("-created_at")
        )

        projects = (
            Project.objects
            .filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(owner__username__icontains=query)
            )
            .select_related("owner")
            .order_by("-created_at")
        )

        users = (
            get_user_model().objects
            .filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(bio__icontains=query)
                | Q(location__icontains=query)
                | Q(skills__icontains=query)
            )
            .filter(is_active=True)
            .order_by("-points", "username")
        )

    context = {
        "query": query,
        "problems": problems,
        "solutions": solutions,
        "projects": projects,
        "users": users,
        "total_results": (
            problems.count()
            + solutions.count()
            + projects.count()
            + users.count()
        ),
    }

    return render(
        request,
        "search/search.html",
        context,
    )