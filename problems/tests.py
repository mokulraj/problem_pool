from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Problem


class ProblemTestMixin:
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
            "title": "A valid test problem",
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


class ProblemListTests(ProblemTestMixin, TestCase):

    def test_problem_list_is_public(self):
        response = self.client.get(
            reverse("problems:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_problem_search_filters_results(self):
        user = self.create_user()

        matching_problem = self.create_problem(
            user,
            title="Long queues in college canteen",
        )

        other_problem = self.create_problem(
            user,
            title="Broken campus transportation system",
        )

        response = self.client.get(
            reverse("problems:list"),
            {"q": "canteen"},
        )

        self.assertContains(
            response,
            matching_problem.title,
        )
        self.assertNotContains(
            response,
            other_problem.title,
        )

    def test_problem_category_filter(self):
        user = self.create_user()

        campus_problem = self.create_problem(
            user,
            title="Campus cafeteria problem",
            category=Problem.Category.CAMPUS,
        )

        technology_problem = self.create_problem(
            user,
            title="Campus technology problem",
            category=Problem.Category.TECHNOLOGY,
        )

        response = self.client.get(
            reverse("problems:list"),
            {"category": Problem.Category.CAMPUS},
        )

        self.assertContains(
            response,
            campus_problem.title,
        )
        self.assertNotContains(
            response,
            technology_problem.title,
        )


class ProblemDetailTests(ProblemTestMixin, TestCase):

    def test_problem_detail_is_public(self):
        user = self.create_user()
        problem = self.create_problem(user)

        response = self.client.get(
            reverse(
                "problems:detail",
                kwargs={"pk": problem.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_problem_detail_increments_view_count(self):
        user = self.create_user()
        problem = self.create_problem(user)

        self.assertEqual(
            problem.views,
            0,
        )

        self.client.get(
            reverse(
                "problems:detail",
                kwargs={"pk": problem.pk},
            )
        )

        problem.refresh_from_db()

        self.assertEqual(
            problem.views,
            1,
        )

    def test_problem_detail_counts_only_one_view_per_session(self):
        user = self.create_user()
        problem = self.create_problem(user)

        detail_url = reverse(
            "problems:detail",
            kwargs={"pk": problem.pk},
        )

        self.client.get(detail_url)
        self.client.get(detail_url)
        self.client.get(detail_url)

        problem.refresh_from_db()

        self.assertEqual(
            problem.views,
            1,
        )


class ProblemCreateTests(ProblemTestMixin, TestCase):

    def test_anonymous_user_cannot_create_problem(self):
        response = self.client.get(
            reverse("problems:create")
        )

        self.assertRedirects(
            response,
            f"/login/?next={reverse('problems:create')}",
        )

    def test_authenticated_user_can_create_problem(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.post(
            reverse("problems:create"),
            {
                "title": "Long queues in college canteen",
                "description": (
                    "Students experience long waiting times "
                    "at the college canteen every day."
                ),
                "category": Problem.Category.CAMPUS,
                "location": "College Campus",
                "priority": Problem.Priority.HIGH,
            },
        )

        problem = Problem.objects.get(
            title="Long queues in college canteen"
        )

        self.assertRedirects(
            response,
            reverse(
                "problems:detail",
                kwargs={"pk": problem.pk},
            ),
        )

        self.assertEqual(
            problem.created_by,
            user,
        )

    def test_problem_creator_is_taken_from_logged_in_user(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )
        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.client.force_login(owner)

        self.client.post(
            reverse("problems:create"),
            {
                "title": "Long queues in college canteen",
                "description": (
                    "Students experience long waiting times "
                    "at the college canteen every day."
                ),
                "category": Problem.Category.CAMPUS,
                "location": "College Campus",
                "priority": Problem.Priority.MEDIUM,
                "created_by": other_user.pk,
            },
        )

        problem = Problem.objects.get(
            title="Long queues in college canteen"
        )

        self.assertEqual(
            problem.created_by,
            owner,
        )


class ProblemEditTests(ProblemTestMixin, TestCase):

    def test_anonymous_user_cannot_edit_problem(self):
        user = self.create_user()
        problem = self.create_problem(user)

        response = self.client.get(
            reverse(
                "problems:edit",
                kwargs={"pk": problem.pk},
            )
        )

        self.assertRedirects(
            response,
            f"/login/?next=/problems/{problem.pk}/edit/",
        )

    def test_owner_can_edit_problem(self):
        user = self.create_user()
        problem = self.create_problem(user)

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "problems:edit",
                kwargs={"pk": problem.pk},
            ),
            {
                "title": "Updated problem title",
                "description": (
                    "This is an updated problem description "
                    "with enough valid characters."
                ),
                "category": Problem.Category.CAMPUS,
                "location": "Updated Campus",
                "priority": Problem.Priority.HIGH,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "problems:detail",
                kwargs={"pk": problem.pk},
            ),
        )

        problem.refresh_from_db()

        self.assertEqual(
            problem.title,
            "Updated problem title",
        )
        self.assertEqual(
            problem.priority,
            Problem.Priority.HIGH,
        )

    def test_non_owner_cannot_edit_problem(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )
        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        problem = self.create_problem(owner)

        self.client.force_login(other_user)

        response = self.client.get(
            reverse(
                "problems:edit",
                kwargs={"pk": problem.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )


class ProblemDeleteTests(ProblemTestMixin, TestCase):

    def test_anonymous_user_cannot_delete_problem(self):
        user = self.create_user()
        problem = self.create_problem(user)

        response = self.client.post(
            reverse(
                "problems:delete",
                kwargs={"pk": problem.pk},
            )
        )

        self.assertRedirects(
            response,
            f"/login/?next=/problems/{problem.pk}/delete/",
        )

    def test_non_owner_cannot_delete_problem(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )
        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        problem = self.create_problem(owner)

        self.client.force_login(other_user)

        response = self.client.post(
            reverse(
                "problems:delete",
                kwargs={"pk": problem.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertTrue(
            Problem.objects.filter(pk=problem.pk).exists()
        )

    def test_owner_can_delete_problem_with_post(self):
        user = self.create_user()
        problem = self.create_problem(user)

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "problems:delete",
                kwargs={"pk": problem.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse("problems:list"),
        )

        self.assertFalse(
            Problem.objects.filter(pk=problem.pk).exists()
        )

    def test_delete_get_does_not_delete_problem(self):
        user = self.create_user()
        problem = self.create_problem(user)

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "problems:delete",
                kwargs={"pk": problem.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            Problem.objects.filter(pk=problem.pk).exists()
        )


class ProblemValidationTests(ProblemTestMixin, TestCase):

    def test_short_title_is_rejected(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.post(
            reverse("problems:create"),
            {
                "title": "Short",
                "description": (
                    "This is a valid description with "
                    "enough characters."
                ),
                "category": Problem.Category.CAMPUS,
                "location": "Campus",
                "priority": Problem.Priority.MEDIUM,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Problem.objects.filter(
                title="Short"
            ).exists()
        )

    def test_short_description_is_rejected(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.post(
            reverse("problems:create"),
            {
                "title": "A valid problem title",
                "description": "Too short",
                "category": Problem.Category.CAMPUS,
                "location": "Campus",
                "priority": Problem.Priority.MEDIUM,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Problem.objects.count(),
            0,
        )