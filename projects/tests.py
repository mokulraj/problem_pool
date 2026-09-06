from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from problems.models import Problem
from solutions.models import Solution

from .models import Project


class ProjectTestMixin:

    def create_user(
        self,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Test",
            last_name="User",
        )

    def create_problem(self, user, **kwargs):
        defaults = {
            "title": "Test problem",
            "description": (
                "This is a valid test problem description "
                "with enough characters."
            ),
            "category": Problem.Category.CAMPUS,
            "location": "Test Campus",
            "priority": Problem.Priority.MEDIUM,
        }

        defaults.update(kwargs)

        return Problem.objects.create(
            created_by=user,
            **defaults,
        )

    def create_solution(
        self,
        problem,
        user,
        status=Solution.Status.SELECTED,
        **kwargs,
    ):
        defaults = {
            "title": "Test selected solution",
            "description": (
                "This is a valid test solution description "
                "with enough characters."
            ),
            "status": status,
        }

        defaults.update(kwargs)

        return Solution.objects.create(
            problem=problem,
            proposed_by=user,
            **defaults,
        )

    def create_project(
        self,
        owner,
        problem,
        solution,
        **kwargs,
    ):
        defaults = {
            "name": "Test project",
            "description": (
                "This is a valid test project description "
                "with enough characters."
            ),
            "status": Project.Status.PLANNING,
        }

        defaults.update(kwargs)

        return Project.objects.create(
            owner=owner,
            problem=problem,
            selected_solution=solution,
            **defaults,
        )


class ProjectListTests(ProjectTestMixin, TestCase):

    def test_project_list_requires_login(self):
        response = self.client.get(
            reverse("projects:list")
        )

        self.assertRedirects(
            response,
            "/login/?next=/projects/",
        )

    def test_authenticated_user_can_view_project_list(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.get(
            reverse("projects:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )


class ProjectDetailTests(ProjectTestMixin, TestCase):

    def test_project_detail_requires_login(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(
            problem,
            user,
        )
        project = self.create_project(
            user,
            problem,
            solution,
        )

        response = self.client.get(
            reverse(
                "projects:detail",
                kwargs={"pk": project.pk},
            )
        )

        self.assertRedirects(
            response,
            f"/login/?next=/projects/{project.pk}/",
        )

    def test_authenticated_user_can_view_project_detail(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        project = self.create_project(
            owner,
            problem,
            solution,
        )

        self.client.force_login(owner)

        response = self.client.get(
            reverse(
                "projects:detail",
                kwargs={"pk": project.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["project"],
            project,
        )


class ProjectCreateTests(ProjectTestMixin, TestCase):

    def test_project_creation_requires_login(self):
        user = self.create_user()

        problem = self.create_problem(user)

        solution = self.create_solution(
            problem,
            user,
        )

        response = self.client.get(
            reverse(
                "projects:create",
                kwargs={"solution_id": solution.pk},
            )
        )

        self.assertRedirects(
            response,
            f"/login/?next=/projects/create/{solution.pk}/",
        )

    def test_only_problem_owner_can_create_project(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        self.client.force_login(other_user)

        response = self.client.get(
            reverse(
                "projects:create",
                kwargs={"solution_id": solution.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            Project.objects.filter(
                problem=problem
            ).exists()
        )

    def test_only_selected_solution_can_create_project(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
            status=Solution.Status.PROPOSED,
        )

        self.client.force_login(owner)

        response = self.client.get(
            reverse(
                "projects:create",
                kwargs={"solution_id": solution.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": solution.pk},
            ),
        )

        self.assertFalse(
            Project.objects.filter(
                problem=problem
            ).exists()
        )

    def test_problem_owner_can_create_project(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        self.client.force_login(owner)

        response = self.client.post(
            reverse(
                "projects:create",
                kwargs={"solution_id": solution.pk},
            ),
            {
                "name": "Campus Improvement Project",
                "description": (
                    "A project to improve the campus "
                    "facilities and services."
                ),
                "start_date": "2026-09-10",
                "end_date": "2026-12-10",
            },
        )

        project = Project.objects.get(
            problem=problem
        )

        self.assertRedirects(
            response,
            reverse(
                "projects:detail",
                kwargs={"pk": project.pk},
            ),
        )

        self.assertEqual(
            project.owner,
            owner,
        )

        self.assertEqual(
            project.selected_solution,
            solution,
        )

        self.assertEqual(
            project.problem,
            problem,
        )

        self.assertEqual(
            project.name,
            "Campus Improvement Project",
        )

        self.assertEqual(
            project.status,
            Project.Status.PLANNING,
        )

    def test_project_creation_cannot_be_duplicated(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        existing_project = self.create_project(
            owner,
            problem,
            solution,
        )

        self.client.force_login(owner)

        response = self.client.post(
            reverse(
                "projects:create",
                kwargs={"solution_id": solution.pk},
            ),
            {
                "name": "Another project",
                "description": (
                    "This duplicate project should "
                    "not be created."
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "projects:detail",
                kwargs={"pk": existing_project.pk},
            ),
        )

        self.assertEqual(
            Project.objects.filter(
                problem=problem
            ).count(),
            1,
        )

    def test_project_creation_requires_valid_dates(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        self.client.force_login(owner)

        response = self.client.post(
            reverse(
                "projects:create",
                kwargs={"solution_id": solution.pk},
            ),
            {
                "name": "Invalid dates project",
                "description": (
                    "This project has an invalid "
                    "date range."
                ),
                "start_date": "2026-12-10",
                "end_date": "2026-09-10",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Project.objects.filter(
                problem=problem
            ).exists()
        )


class ProjectEditTests(ProjectTestMixin, TestCase):

    def test_project_owner_can_edit_project(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        project = self.create_project(
            owner,
            problem,
            solution,
        )

        self.client.force_login(owner)

        response = self.client.post(
            reverse(
                "projects:edit",
                kwargs={"pk": project.pk},
            ),
            {
                "name": "Updated project",
                "description": (
                    "Updated project description "
                    "with enough valid characters."
                ),
                "start_date": "2026-09-15",
                "end_date": "2026-12-15",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "projects:detail",
                kwargs={"pk": project.pk},
            ),
        )

        project.refresh_from_db()

        self.assertEqual(
            project.name,
            "Updated project",
        )

        self.assertEqual(
            project.start_date,
            date(2026, 9, 15),
        )

        self.assertEqual(
            project.end_date,
            date(2026, 12, 15),
        )

    def test_non_owner_cannot_edit_project(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        project = self.create_project(
            owner,
            problem,
            solution,
        )

        self.client.force_login(other_user)

        response = self.client.get(
            reverse(
                "projects:edit",
                kwargs={"pk": project.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_project_status_cannot_be_changed_through_form(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        project = self.create_project(
            owner,
            problem,
            solution,
            status=Project.Status.PLANNING,
        )

        self.client.force_login(owner)

        self.client.post(
            reverse(
                "projects:edit",
                kwargs={"pk": project.pk},
            ),
            {
                "name": "Updated project",
                "description": (
                    "Updated project description "
                    "with enough valid characters."
                ),
                "start_date": "2026-09-15",
                "end_date": "2026-12-15",
                "status": Project.Status.COMPLETED,
            },
        )

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.PLANNING,
        )

    def test_project_completion_can_award_points(self):
        owner = self.create_user()

        problem = self.create_problem(owner)

        solution = self.create_solution(
            problem,
            owner,
        )

        project = self.create_project(
            owner,
            problem,
            solution,
        )

        self.client.force_login(owner)

        self.client.post(
            reverse(
                "projects:edit",
                kwargs={"pk": project.pk},
            ),
            {
                "name": "Completed project",
                "description": (
                    "Completed project description "
                    "with enough valid characters."
                ),
                "start_date": "2026-09-01",
                "end_date": "2026-12-01",
            },
        )

        project.refresh_from_db()

        self.assertNotEqual(
            project.status,
            Project.Status.COMPLETED,
        )