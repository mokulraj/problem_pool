from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from comments.models import Comment
from problems.models import Problem
from projects.models import Project
from solutions.models import Solution
from tasks.models import Task
from teams.models import JoinRequest, TeamMembership


@login_required
def dashboard(request):
    user = request.user

    problems_created = Problem.objects.filter(
        created_by=user,
    ).count()

    solutions_submitted = Solution.objects.filter(
        proposed_by=user,
    ).count()

    projects_owned = Project.objects.filter(
        owner=user,
    ).count()

    projects_joined = TeamMembership.objects.filter(
        user=user,
    ).count()

    pending_join_requests = JoinRequest.objects.filter(
        user=user,
        status=JoinRequest.Status.PENDING,
    ).count()

    completed_tasks = Task.objects.filter(
        assigned_to=user,
        status=Task.Status.COMPLETED,
    ).count()

    active_tasks = Task.objects.filter(
        assigned_to=user,
        status=Task.Status.IN_PROGRESS,
    ).count()

    recent_projects = (
        Project.objects
        .filter(
            Q(owner=user)
            | Q(team_memberships__user=user)
        )
        .select_related(
            "owner",
            "problem",
            "selected_solution",
        )
        .distinct()
        .order_by("-created_at")[:6]
    )

    recent_problems = (
        Problem.objects
        .filter(created_by=user)
        .order_by("-created_at")[:5]
    )

    recent_solutions = (
        Solution.objects
        .filter(proposed_by=user)
        .select_related("problem")
        .order_by("-created_at")[:5]
    )

    pending_requests_for_owner = (
        JoinRequest.objects
        .filter(
            project__owner=user,
            status=JoinRequest.Status.PENDING,
        )
        .select_related(
            "project",
            "user",
        )
        .order_by("-created_at")[:5]
    )

    recent_comments = (
        Comment.objects
        .filter(user=user)
        .select_related(
            "problem",
            "solution",
        )
        .order_by("-created_at")[:5]
    )

    context = {
        "problems_created": problems_created,
        "solutions_submitted": solutions_submitted,
        "projects_owned": projects_owned,
        "projects_joined": projects_joined,
        "pending_join_requests": pending_join_requests,
        "completed_tasks": completed_tasks,
        "active_tasks": active_tasks,
        "recent_projects": recent_projects,
        "recent_problems": recent_problems,
        "recent_solutions": recent_solutions,
        "pending_requests_for_owner": pending_requests_for_owner,
        "recent_comments": recent_comments,

        # Reputation
        "reputation_points": user.points,
        "reputation_level": user.level,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )