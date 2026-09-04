from django.conf import settings
from django.db import models


class Solution(models.Model):

    class Status(models.TextChoices):
        PROPOSED = "PROPOSED", "Proposed"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"

    problem = models.ForeignKey(
        "problems.Problem",
        on_delete=models.CASCADE,
        related_name="solutions",
    )

    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solutions",
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROPOSED,
        db_index=True,
    )

    upvotes = models.PositiveIntegerField(
        default=0
    )

    downvotes = models.PositiveIntegerField(
        default=0
    )

    score = models.IntegerField(
        default=0,
        db_index=True,
    )

    class Meta:
        ordering = [
            "-score",
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=["problem", "-score"]
            ),
            models.Index(
                fields=["problem", "created_at"]
            ),
            models.Index(
                fields=["status", "created_at"]
            ),
        ]

    def __str__(self):
        return self.title

    def update_score(self):
        self.score = self.upvotes - self.downvotes

        self.save(
            update_fields=["score"]
        )