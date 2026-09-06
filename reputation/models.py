from django.conf import settings
from django.db import models


class ReputationReward(models.Model):

    class RewardType(models.TextChoices):
        PROBLEM_CREATED = "PROBLEM_CREATED", "Problem Created"
        SOLUTION_PROPOSED = "SOLUTION_PROPOSED", "Solution Proposed"
        UPVOTE_RECEIVED = "UPVOTE_RECEIVED", "Upvote Received"
        SOLUTION_SELECTED = "SOLUTION_SELECTED", "Solution Selected"
        TASK_COMPLETED = "TASK_COMPLETED", "Task Completed"
        PROJECT_COMPLETED = "PROJECT_COMPLETED", "Project Completed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reputation_rewards",
    )

    reward_type = models.CharField(
        max_length=30,
        choices=RewardType.choices,
    )

    points = models.PositiveIntegerField()

    reference_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "reward_type",
                    "reference_id",
                ],
                name="unique_user_reward_reference",
            ),
        ]

        indexes = [
            models.Index(
                fields=["user", "reward_type"],
            ),
            models.Index(
                fields=["user", "created_at"],
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.get_reward_type_display()} - "
            f"{self.points} points"
        )