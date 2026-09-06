from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from projects.models import Project
from .models import ReputationReward


@login_required
def leaderboard(request):
    User = get_user_model()

    leaderboard_users = (
        User.objects
        .filter(is_active=True)
        .annotate(
            problems_created_count=Count(
                "problems",
                distinct=True,
            ),
            solutions_submitted_count=Count(
                "solutions",
                distinct=True,
            ),
            projects_owned_count=Count(
                "owned_projects",
                distinct=True,
            ),
            projects_completed_count=Count(
                "owned_projects",
                filter=Q(
                    owned_projects__status=Project.Status.COMPLETED,
                ),
                distinct=True,
            ),
        )
        .order_by(
            "-points",
            "username",
        )
    )

    top_users = list(
        leaderboard_users[:10]
    )

    current_user_position = (
        leaderboard_users
        .filter(
            points__gt=request.user.points,
        )
        .count()
        + 1
    )

    for index, user in enumerate(top_users, start=1):
        user.leaderboard_rank = index

    context = {
        "top_users": top_users,
        "current_user_position": current_user_position,
        "current_user": request.user,
    }

    return render(
        request,
        "reputation/leaderboard.html",
        context,
    )