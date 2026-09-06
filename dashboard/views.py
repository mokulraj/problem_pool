from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from comments.models import Comment
from notifications.models import Notification
from problems.models import Problem
from projects.models import Project
from solutions.models import Solution
from tasks.models import Task
from teams.models import JoinRequest, TeamMembership


@login_required
def dashboard(request):
    user = request.user
    User = get_user_model()

    # =========================================================
    # PERSONAL STATISTICS
    # =========================================================

    problems_created = Problem.objects.filter(
        created_by=user,
    ).count()

    solutions_submitted = Solution.objects.filter(
        proposed_by=user,
    ).count()

    selected_solutions = Solution.objects.filter(
        proposed_by=user,
        status=Solution.Status.SELECTED,
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

    todo_tasks = Task.objects.filter(
        assigned_to=user,
        status=Task.Status.TODO,
    ).count()

    total_assigned_tasks = Task.objects.filter(
        assigned_to=user,
    ).count()

    task_completion_percentage = (
        round((completed_tasks / total_assigned_tasks) * 100)
        if total_assigned_tasks
        else 0
    )

    # =========================================================
    # PLATFORM STATISTICS
    # =========================================================

    total_users = User.objects.filter(
        is_active=True,
    ).count()

    total_problems = Problem.objects.count()

    total_solutions = Solution.objects.count()

    total_selected_solutions = Solution.objects.filter(
        status=Solution.Status.SELECTED,
    ).count()

    total_projects = Project.objects.count()

    total_active_projects = Project.objects.filter(
        status=Project.Status.ACTIVE,
    ).count()

    total_completed_projects = Project.objects.filter(
        status=Project.Status.COMPLETED,
    ).count()

    total_tasks = Task.objects.count()

    total_completed_tasks = Task.objects.filter(
        status=Task.Status.COMPLETED,
    ).count()

    total_in_progress_tasks = Task.objects.filter(
        status=Task.Status.IN_PROGRESS,
    ).count()

    total_team_memberships = TeamMembership.objects.count()

    # =========================================================
    # PERSONAL RECENT CONTENT
    # =========================================================

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

    # =========================================================
    # RECENT NOTIFICATIONS
    # =========================================================

    recent_notifications = (
        Notification.objects
        .filter(recipient=user)
        .select_related(
            "related_problem",
            "related_solution",
            "related_project",
        )
        .order_by("-created_at")[:6]
    )

    unread_notifications = Notification.objects.filter(
        recipient=user,
        is_read=False,
    ).count()

    # =========================================================
    # TEAM ACTIVITY
    # =========================================================

    recent_team_activity = (
        TeamMembership.objects
        .filter(project__owner=user)
        .select_related(
            "user",
            "project",
        )
        .order_by("-joined_at")[:6]
    )

    recent_join_requests = (
        JoinRequest.objects
        .filter(
            project__owner=user,
        )
        .select_related(
            "user",
            "project",
        )
        .order_by("-created_at")[:6]
    )

    # =========================================================
    # RECENT USER ACTIVITY
    # =========================================================

    recent_activity = []

    for problem in Problem.objects.filter(
        created_by=user,
    ).order_by("-created_at")[:5]:
        recent_activity.append({
            "type": "problem",
            "title": problem.title,
            "created_at": problem.created_at,
            "url_name": "problems:detail",
            "object_id": problem.pk,
            "icon": "bi-question-circle",
        })

    for solution in Solution.objects.filter(
        proposed_by=user,
    ).select_related(
        "problem",
    ).order_by("-created_at")[:5]:
        recent_activity.append({
            "type": "solution",
            "title": solution.title,
            "created_at": solution.created_at,
            "url_name": "solutions:detail",
            "object_id": solution.pk,
            "icon": "bi-lightbulb",
        })

    for comment in Comment.objects.filter(
        user=user,
    ).select_related(
        "problem",
        "solution",
    ).order_by("-created_at")[:5]:
        if comment.problem:
            activity_title = comment.problem.title
        elif comment.solution:
            activity_title = comment.solution.title
        else:
            activity_title = "Comment"

        recent_activity.append({
            "type": "comment",
            "title": activity_title,
            "created_at": comment.created_at,
            "url_name": None,
            "object_id": None,
            "icon": "bi-chat-left-text",
        })

    recent_activity.sort(
        key=lambda item: item["created_at"],
        reverse=True,
    )

    recent_activity = recent_activity[:8]

    # =========================================================
    # CHART DATA
    # =========================================================

    today = timezone.localdate()

    activity_labels = []
    activity_problems = []
    activity_solutions = []
    activity_tasks = []

    for days_ago in range(6, -1, -1):
        current_date = today - timedelta(days=days_ago)

        next_date = current_date + timedelta(days=1)

        activity_labels.append(
            current_date.strftime("%d %b")
        )

        activity_problems.append(
            Problem.objects.filter(
                created_by=user,
                created_at__gte=current_date,
                created_at__lt=next_date,
            ).count()
        )

        activity_solutions.append(
            Solution.objects.filter(
                proposed_by=user,
                created_at__gte=current_date,
                created_at__lt=next_date,
            ).count()
        )

        activity_tasks.append(
            Task.objects.filter(
                assigned_to=user,
                status=Task.Status.COMPLETED,
                updated_at__gte=current_date,
                updated_at__lt=next_date,
            ).count()
        )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        # Personal statistics
        "problems_created": problems_created,
        "solutions_submitted": solutions_submitted,
        "selected_solutions": selected_solutions,
        "projects_owned": projects_owned,
        "projects_joined": projects_joined,
        "pending_join_requests": pending_join_requests,
        "completed_tasks": completed_tasks,
        "active_tasks": active_tasks,
        "todo_tasks": todo_tasks,
        "total_assigned_tasks": total_assigned_tasks,
        "task_completion_percentage": task_completion_percentage,

        # Platform statistics
        "total_users": total_users,
        "total_problems": total_problems,
        "total_solutions": total_solutions,
        "total_selected_solutions": total_selected_solutions,
        "total_projects": total_projects,
        "total_active_projects": total_active_projects,
        "total_completed_projects": total_completed_projects,
        "total_tasks": total_tasks,
        "total_completed_tasks": total_completed_tasks,
        "total_in_progress_tasks": total_in_progress_tasks,
        "total_team_memberships": total_team_memberships,

        # Recent content
        "recent_projects": recent_projects,
        "recent_problems": recent_problems,
        "recent_solutions": recent_solutions,
        "pending_requests_for_owner": pending_requests_for_owner,
        "recent_comments": recent_comments,

        # Notifications
        "recent_notifications": recent_notifications,
        "unread_notifications": unread_notifications,

        # Team activity
        "recent_team_activity": recent_team_activity,
        "recent_join_requests": recent_join_requests,

        # Activity feed
        "recent_activity": recent_activity,

        # Charts
        "activity_labels": activity_labels,
        "activity_problems": activity_problems,
        "activity_solutions": activity_solutions,
        "activity_tasks": activity_tasks,

        # Reputation
        "reputation_points": user.points,
        "reputation_level": user.level,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )