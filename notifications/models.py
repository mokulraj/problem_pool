from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        SOLUTION_PROPOSED = "SOLUTION_PROPOSED", "Solution Proposed"
        COMMENT = "COMMENT", "Comment"
        VOTE = "VOTE", "Solution Vote"
        SOLUTION_SELECTED = "SOLUTION_SELECTED", "Solution Selected"
        JOIN_REQUEST = "JOIN_REQUEST", "Join Request"
        JOIN_APPROVED = "JOIN_APPROVED", "Join Approved"
        TASK_ASSIGNED = "TASK_ASSIGNED", "Task Assigned"
        TASK_STATUS_UPDATED = (
            "TASK_STATUS_UPDATED",
            "Task Status Updated",
        )
        PROJECT_COMPLETED = "PROJECT_COMPLETED", "Project Completed"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        db_index=True,
    )

    related_problem = models.ForeignKey(
        "problems.Problem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    related_solution = models.ForeignKey(
        "solutions.Solution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    related_project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    is_read = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"]
            ),
            models.Index(
                fields=["recipient", "-created_at"]
            ),
            models.Index(
                fields=["notification_type", "-created_at"]
            ),
        ]

    def __str__(self):
        return f"{self.recipient.username}: {self.message}"