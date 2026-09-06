from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from comments.models import Comment
from projects.models import Project
from solutions.models import Solution, Vote
from tasks.models import Task
from teams.models import JoinRequest

from .models import Notification
from .utils import create_notification


# =========================================================
# SOLUTION NOTIFICATIONS
# =========================================================

@receiver(pre_save, sender=Solution)
def solution_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )


@receiver(post_save, sender=Solution)
def solution_post_save(sender, instance, created, **kwargs):
    problem = instance.problem

    # Someone proposed a solution to your problem
    if created:
        create_notification(
            recipient=problem.created_by,
            actor=instance.proposed_by,
            message=(
                f"{instance.proposed_by.username} proposed a solution "
                f"for your problem: {problem.title}"
            ),
            notification_type=Notification.NotificationType.SOLUTION_PROPOSED,
            problem=problem,
            solution=instance,
        )

    # Your solution was selected
    previous_status = getattr(instance, "_previous_status", None)

    if (
        instance.status == Solution.Status.SELECTED
        and previous_status != Solution.Status.SELECTED
    ):
        create_notification(
            recipient=instance.proposed_by,
            actor=problem.created_by,
            message=(
                f"Your solution '{instance.title}' was selected "
                f"for the problem: {problem.title}"
            ),
            notification_type=Notification.NotificationType.SOLUTION_SELECTED,
            problem=problem,
            solution=instance,
        )


# =========================================================
# VOTING NOTIFICATIONS
# =========================================================

@receiver(post_save, sender=Vote)
def vote_post_save(sender, instance, created, **kwargs):
    solution = instance.solution

    vote_text = (
        "upvoted"
        if instance.vote_type == Vote.VoteType.UP
        else "downvoted"
    )

    create_notification(
        recipient=solution.proposed_by,
        actor=instance.user,
        message=(
            f"{instance.user.username} {vote_text} your solution: "
            f"{solution.title}"
        ),
        notification_type=Notification.NotificationType.VOTE,
        problem=solution.problem,
        solution=solution,
    )


# =========================================================
# COMMENT NOTIFICATIONS
# =========================================================

@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    if not created:
        return

    # Comment on a problem
    if instance.problem_id:
        problem = instance.problem

        create_notification(
            recipient=problem.created_by,
            actor=instance.user,
            message=(
                f"{instance.user.username} commented on your problem: "
                f"{problem.title}"
            ),
            notification_type=Notification.NotificationType.COMMENT,
            problem=problem,
        )

    # Comment on a solution
    elif instance.solution_id:
        solution = instance.solution

        create_notification(
            recipient=solution.proposed_by,
            actor=instance.user,
            message=(
                f"{instance.user.username} commented on your solution: "
                f"{solution.title}"
            ),
            notification_type=Notification.NotificationType.COMMENT,
            problem=solution.problem,
            solution=solution,
        )


# =========================================================
# JOIN REQUEST NOTIFICATIONS
# =========================================================

@receiver(pre_save, sender=JoinRequest)
def join_request_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )


@receiver(post_save, sender=JoinRequest)
def join_request_post_save(sender, instance, created, **kwargs):
    project = instance.project

    # Someone requested to join your project
    if created and instance.status == JoinRequest.Status.PENDING:
        create_notification(
            recipient=project.owner,
            actor=instance.user,
            message=(
                f"{instance.user.username} requested to join "
                f"your project: {project.name}"
            ),
            notification_type=Notification.NotificationType.JOIN_REQUEST,
            project=project,
        )

    # Join request approved
    previous_status = getattr(instance, "_previous_status", None)

    if (
        instance.status == JoinRequest.Status.APPROVED
        and previous_status != JoinRequest.Status.APPROVED
    ):
        create_notification(
            recipient=instance.user,
            actor=project.owner,
            message=(
                f"Your request to join '{project.name}' "
                f"has been approved."
            ),
            notification_type=Notification.NotificationType.JOIN_APPROVED,
            project=project,
        )


# =========================================================
# TASK ASSIGNMENT NOTIFICATIONS
# =========================================================

@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_assignee_id = None
        return

    instance._previous_assignee_id = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list("assigned_to_id", flat=True)
        .first()
    )


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    if not instance.assigned_to_id:
        return

    previous_assignee_id = getattr(
        instance,
        "_previous_assignee_id",
        None,
    )

    # Notify when task is newly assigned or reassigned
    if created or previous_assignee_id != instance.assigned_to_id:
        create_notification(
            recipient=instance.assigned_to,
            message=(
                f"You have been assigned a task: "
                f"{instance.title}"
            ),
            notification_type=Notification.NotificationType.TASK_ASSIGNED,
            project=instance.project,
        )


# =========================================================
# PROJECT COMPLETION NOTIFICATIONS
# =========================================================

@receiver(pre_save, sender=Project)
def project_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )


@receiver(post_save, sender=Project)
def project_post_save(sender, instance, created, **kwargs):
    previous_status = getattr(
        instance,
        "_previous_status",
        None,
    )

    if (
        instance.status != Project.Status.COMPLETED
        or previous_status == Project.Status.COMPLETED
    ):
        return

    # Notify project owner
    create_notification(
        recipient=instance.owner,
        message=(
            f"Project '{instance.name}' has been completed."
        ),
        notification_type=Notification.NotificationType.PROJECT_COMPLETED,
        project=instance,
    )

    # Notify approved team members
    team_members = (
        instance.team_memberships
        .select_related("user")
        .exclude(user=instance.owner)
    )

    for membership in team_members:
        create_notification(
            recipient=membership.user,
            message=(
                f"Project '{instance.name}' has been completed."
            ),
            notification_type=Notification.NotificationType.PROJECT_COMPLETED,
            project=instance,
        )