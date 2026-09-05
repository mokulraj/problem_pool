from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TeamMembership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "MEMBER", "Member"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["joined_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_team_member",
            ),
        ]

        indexes = [
            models.Index(
                fields=["project", "joined_at"],
            ),
            models.Index(
                fields=["user", "joined_at"],
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"


class JoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="join_requests",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_join_requests",
    )

    message = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["project", "status", "created_at"],
            ),
            models.Index(
                fields=["user", "status", "created_at"],
            ),
        ]

    def clean(self):
        if not self.project_id or not self.user_id:
            return

        if self.project.owner_id == self.user_id:
            raise ValidationError(
                "The project owner cannot request to join their own project."
            )

        if TeamMembership.objects.filter(
            project=self.project,
            user=self.user,
        ).exists():
            raise ValidationError(
                "This user is already a member of the project."
            )

    def __str__(self):
        return f"{self.user.username} → {self.project.name}"