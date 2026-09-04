from django.conf import settings
from django.db import models


class Problem(models.Model):

    class Category(models.TextChoices):
        EDUCATION = "EDUCATION", "Education"
        TECHNOLOGY = "TECHNOLOGY", "Technology"
        ENVIRONMENT = "ENVIRONMENT", "Environment"
        TRANSPORTATION = "TRANSPORTATION", "Transportation"
        HEALTHCARE = "HEALTHCARE", "Healthcare"
        COMMUNITY = "COMMUNITY", "Community"
        BUSINESS = "BUSINESS", "Business"
        AGRICULTURE = "AGRICULTURE", "Agriculture"
        CAMPUS = "CAMPUS", "Campus"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SOLVED = "SOLVED", "Solved"
        CLOSED = "CLOSED", "Closed"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
    )

    location = models.CharField(
        max_length=150,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="problems",
    )

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
        default=Status.OPEN,
        db_index=True,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )

    views = models.PositiveIntegerField(
        default=0
    )

    solution_count = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["status", "created_at"]
            ),
            models.Index(
                fields=["category", "created_at"]
            ),
            models.Index(
                fields=["priority", "created_at"]
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def status_display(self):
        return self.get_status_display()

    @property
    def category_display(self):
        return self.get_category_display()

    @property
    def priority_display(self):
        return self.get_priority_display()