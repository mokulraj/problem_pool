from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = "PLANNING", "Planning"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    problem = models.OneToOneField(
        "problems.Problem",
        on_delete=models.PROTECT,
        related_name="project",
    )

    selected_solution = models.OneToOneField(
        "solutions.Solution",
        on_delete=models.PROTECT,
        related_name="project",
    )

    name = models.CharField(max_length=200)

    description = models.TextField()

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_projects",
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return self.name

    @property
    def progress(self):
        """
        Progress will be calculated from project tasks.

        Tasks are implemented in a later module.
        Until tasks exist, progress is 0%.
        """
        tasks = getattr(self, "tasks", None)

        if tasks is None:
            return 0

        total_tasks = tasks.count()

        if total_tasks == 0:
            return 0

        completed_tasks = tasks.filter(
            status="COMPLETED"
        ).count()

        return round((completed_tasks / total_tasks) * 100)