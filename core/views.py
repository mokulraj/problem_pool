from django.shortcuts import render

from problems.models import Problem


def home(request):

    trending_problems = (
        Problem.objects
        .select_related("created_by")
        .order_by("-views", "-created_at")[:3]
    )

    latest_problems = (
        Problem.objects
        .select_related("created_by")
        .order_by("-created_at")[:3]
    )

    context = {
        "trending_problems": trending_problems,
        "latest_problems": latest_problems,
    }

    return render(
        request,
        "home.html",
        context
    )