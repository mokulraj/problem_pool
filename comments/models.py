from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Comment(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    problem = models.ForeignKey(
        "problems.Problem",
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    solution = models.ForeignKey(
        "solutions.Solution",
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "created_at",
        ]

        indexes = [
            models.Index(
                fields=["problem", "created_at"]
            ),
            models.Index(
                fields=["solution", "created_at"]
            ),
            models.Index(
                fields=["user", "created_at"]
            ),
        ]

    def clean(self):

        if self.problem_id and self.solution_id:
            raise ValidationError(
                "A comment cannot belong to both a problem and a solution."
            )

        if not self.problem_id and not self.solution_id:
            raise ValidationError(
                "A comment must belong to a problem or a solution."
            )

    def __str__(self):
        return (
            f"{self.user.username}: "
            f"{self.content[:50]}"
        )