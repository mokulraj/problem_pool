from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        db_index=True,
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "status",
            "due_date",
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=["project", "status"],
            ),
            models.Index(
                fields=["assigned_to", "status"],
            ),
            models.Index(
                fields=["project", "due_date"],
            ),
        ]

    def clean(self):
        if self.due_date and self.project_id:
            if (
                self.project.end_date
                and self.due_date > self.project.end_date
            ):
                raise ValidationError(
                    "Task due date cannot be after the project deadline."
                )

    def __str__(self):
        return self.title