from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        USER = "USER", "User"
        PROBLEM_OWNER = "PROBLEM_OWNER", "Problem Owner"
        TEAM_MEMBER = "TEAM_MEMBER", "Team Member"
        ADMIN = "ADMIN", "Admin"

    email = models.EmailField(
        unique=True
    )

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    bio = models.TextField(
        blank=True
    )

    location = models.CharField(
        max_length=150,
        blank=True
    )

    skills = models.TextField(
        blank=True,
        help_text="Enter skills separated by commas."
    )

    points = models.PositiveIntegerField(
        default=0
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER
    )

    date_joined = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.username

    @property
    def level(self):
        if self.points >= 500:
            return "Community Leader"

        if self.points >= 300:
            return "Expert"

        if self.points >= 150:
            return "Problem Solver"

        if self.points >= 50:
            return "Contributor"

        return "Newcomer"

    @property
    def skill_list(self):
        if not self.skills:
            return []

        return [
            skill.strip()
            for skill in self.skills.split(",")
            if skill.strip()
        ]