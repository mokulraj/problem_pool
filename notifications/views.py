from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list(request):

    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related(
            "related_problem",
            "related_solution",
            "related_project",
        )
        .order_by("-created_at")
    )

    # ---------------------------------------------------------
    # FILTER
    # ---------------------------------------------------------

    filter_type = request.GET.get("filter", "all")

    if filter_type == "unread":

        notifications = notifications.filter(
            is_read=False
        )

    elif filter_type == "problems":

        notifications = notifications.filter(
            related_problem__isnull=False
        )

    elif filter_type == "solutions":

        notifications = notifications.filter(
            related_solution__isnull=False
        )

    elif filter_type == "projects":

        notifications = notifications.filter(
            related_project__isnull=False
        )

    elif filter_type == "system":

        notifications = notifications.filter(
            related_problem__isnull=True,
            related_solution__isnull=True,
            related_project__isnull=True,
        )

    # ---------------------------------------------------------
    # COUNTS
    # ---------------------------------------------------------

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    problem_count = Notification.objects.filter(
        recipient=request.user,
        related_problem__isnull=False,
    ).count()

    solution_count = Notification.objects.filter(
        recipient=request.user,
        related_solution__isnull=False,
    ).count()

    project_count = Notification.objects.filter(
        recipient=request.user,
        related_project__isnull=False,
    ).count()

    system_count = Notification.objects.filter(
        recipient=request.user,
        related_problem__isnull=True,
        related_solution__isnull=True,
        related_project__isnull=True,
    ).count()

    context = {
        "notifications": notifications,
        "active_filter": filter_type,

        "unread_count": unread_count,
        "problem_count": problem_count,
        "solution_count": solution_count,
        "project_count": project_count,
        "system_count": system_count,
    }

    return render(
        request,
        "notifications/notification_list.html",
        context,
    )


@login_required
def mark_read(request, pk):

    if request.method != "POST":
        return redirect("notifications:list")

    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )

    notification.is_read = True

    notification.save(
        update_fields=["is_read"]
    )

    messages.success(
        request,
        "Notification marked as read."
    )

    return redirect("notifications:list")


@login_required
def mark_all_read(request):

    if request.method != "POST":
        return redirect("notifications:list")

    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(
        is_read=True
    )

    messages.success(
        request,
        "All notifications marked as read."
    )

    return redirect("notifications:list")