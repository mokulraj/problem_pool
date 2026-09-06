from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from problems.models import Problem
from solutions.models import Solution

from .models import Comment


class CommentTestMixin:

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

    def create_problem(self, user):
        return Problem.objects.create(
            title="Test problem",
            description=(
                "This is a valid test problem description "
                "with enough characters."
            ),
            category=Problem.Category.CAMPUS,
            location="Test Campus",
            priority=Problem.Priority.MEDIUM,
            created_by=user,
        )

    def create_solution(self, problem, user):
        return Solution.objects.create(
            problem=problem,
            proposed_by=user,
            title="Test solution",
            description=(
                "This is a valid test solution description "
                "with enough characters."
            ),
        )

    def create_problem_comment(self, user, problem):
        return Comment.objects.create(
            user=user,
            problem=problem,
            content="This is a test comment.",
        )

    def create_solution_comment(self, user, solution):
        return Comment.objects.create(
            user=user,
            solution=solution,
            content="This is a test comment.",
        )


class CommentCreateTests(CommentTestMixin, TestCase):

    def test_anonymous_user_cannot_create_comment(self):
        user = self.create_user()
        problem = self.create_problem(user)

        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": problem.pk,
                "content": "Test comment.",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            response.url.startswith("/login/")
        )

        self.assertEqual(
            Comment.objects.count(),
            0,
        )

    def test_get_request_is_rejected(self):
        user = self.create_user()
        problem = self.create_problem(user)

        self.client.force_login(user)

        response = self.client.get(
            reverse("comments:create"),
            {
                "problem_id": problem.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse("problems:list"),
        )

        self.assertEqual(
            Comment.objects.count(),
            0,
        )

    def test_authenticated_user_can_comment_on_problem(self):
        user = self.create_user()
        problem = self.create_problem(user)

        self.client.force_login(user)

        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": problem.pk,
                "content": "This is a problem comment.",
                "next": reverse(
                    "problems:detail",
                    kwargs={"pk": problem.pk},
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "problems:detail",
                kwargs={"pk": problem.pk},
            ),
        )

        comment = Comment.objects.get()

        self.assertEqual(
            comment.user,
            user,
        )

        self.assertEqual(
            comment.problem,
            problem,
        )

        self.assertIsNone(
            comment.solution
        )

        self.assertEqual(
            comment.content,
            "This is a problem comment.",
        )

    def test_authenticated_user_can_comment_on_solution(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(
            problem,
            user,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("comments:create"),
            {
                "solution_id": solution.pk,
                "content": "This is a solution comment.",
                "next": reverse(
                    "solutions:detail",
                    kwargs={"pk": solution.pk},
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": solution.pk},
            ),
        )

        comment = Comment.objects.get()

        self.assertEqual(
            comment.user,
            user,
        )

        self.assertEqual(
            comment.solution,
            solution,
        )

        self.assertIsNone(
            comment.problem
        )

    def test_comment_requires_target(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.post(
            reverse("comments:create"),
            {
                "content": "Comment without target.",
            },
        )

        self.assertRedirects(
            response,
            reverse("problems:list"),
        )

        self.assertEqual(
            Comment.objects.count(),
            0,
        )

    def test_comment_cannot_target_problem_and_solution(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(
            problem,
            user,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": problem.pk,
                "solution_id": solution.pk,
                "content": "Invalid target comment.",
            },
        )

        self.assertRedirects(
            response,
            reverse("problems:list"),
        )

        self.assertEqual(
            Comment.objects.count(),
            0,
        )

    def test_invalid_problem_id_returns_404(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": 999999,
                "content": "Test comment.",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_invalid_solution_id_returns_404(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.post(
            reverse("comments:create"),
            {
                "solution_id": 999999,
                "content": "Test comment.",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class CommentValidationTests(CommentTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()
        self.problem = self.create_problem(
            self.user
        )

        self.client.force_login(self.user)

    def test_comment_shorter_than_three_characters_is_rejected(self):
        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": self.problem.pk,
                "content": "ab",
            },
        )

        self.assertRedirects(
            response,
            reverse("problems:list"),
        )

        self.assertEqual(
            Comment.objects.count(),
            0,
        )

    def test_comment_longer_than_2000_characters_is_rejected(self):
        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": self.problem.pk,
                "content": "a" * 2001,
            },
        )

        self.assertRedirects(
            response,
            reverse("problems:list"),
        )

        self.assertEqual(
            Comment.objects.count(),
            0,
        )

    def test_comment_with_exactly_three_characters_is_valid(self):
        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": self.problem.pk,
                "content": "abc",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            Comment.objects.count(),
            1,
        )

    def test_comment_with_exactly_2000_characters_is_valid(self):
        response = self.client.post(
            reverse("comments:create"),
            {
                "problem_id": self.problem.pk,
                "content": "a" * 2000,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            Comment.objects.count(),
            1,
        )

    def test_comment_content_is_stripped(self):
        self.client.post(
            reverse("comments:create"),
            {
                "problem_id": self.problem.pk,
                "content": "   Valid comment   ",
            },
        )

        comment = Comment.objects.get()

        self.assertEqual(
            comment.content,
            "Valid comment",
        )


class CommentEditTests(CommentTestMixin, TestCase):

    def test_comment_owner_can_edit_comment(self):
        user = self.create_user()
        problem = self.create_problem(user)
        comment = self.create_problem_comment(
            user,
            problem,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "comments:edit",
                kwargs={"pk": comment.pk},
            ),
            {
                "content": "Updated comment.",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "problems:detail",
                kwargs={"pk": problem.pk},
            ),
        )

        comment.refresh_from_db()

        self.assertEqual(
            comment.content,
            "Updated comment.",
        )

    def test_comment_owner_can_edit_solution_comment(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(
            problem,
            user,
        )

        comment = self.create_solution_comment(
            user,
            solution,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "comments:edit",
                kwargs={"pk": comment.pk},
            ),
            {
                "content": "Updated solution comment.",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": solution.pk},
            ),
        )

        comment.refresh_from_db()

        self.assertEqual(
            comment.content,
            "Updated solution comment.",
        )

    def test_non_owner_cannot_edit_comment(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        problem = self.create_problem(owner)

        comment = self.create_problem_comment(
            owner,
            problem,
        )

        self.client.force_login(other_user)

        response = self.client.get(
            reverse(
                "comments:edit",
                kwargs={"pk": comment.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        comment.refresh_from_db()

        self.assertEqual(
            comment.content,
            "This is a test comment.",
        )

    def test_get_edit_page_is_available_to_owner(self):
        user = self.create_user()
        problem = self.create_problem(user)

        comment = self.create_problem_comment(
            user,
            problem,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "comments:edit",
                kwargs={"pk": comment.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )


class CommentDeleteTests(CommentTestMixin, TestCase):

    def test_comment_owner_can_delete_problem_comment(self):
        user = self.create_user()
        problem = self.create_problem(user)

        comment = self.create_problem_comment(
            user,
            problem,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "comments:delete",
                kwargs={"pk": comment.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "problems:detail",
                kwargs={"pk": problem.pk},
            ),
        )

        self.assertFalse(
            Comment.objects.filter(
                pk=comment.pk
            ).exists()
        )

    def test_comment_owner_can_delete_solution_comment(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(
            problem,
            user,
        )

        comment = self.create_solution_comment(
            user,
            solution,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "comments:delete",
                kwargs={"pk": comment.pk},
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
            Comment.objects.filter(
                pk=comment.pk
            ).exists()
        )

    def test_non_owner_cannot_delete_comment(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        problem = self.create_problem(owner)

        comment = self.create_problem_comment(
            owner,
            problem,
        )

        self.client.force_login(other_user)

        response = self.client.post(
            reverse(
                "comments:delete",
                kwargs={"pk": comment.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertTrue(
            Comment.objects.filter(
                pk=comment.pk
            ).exists()
        )

    def test_delete_requires_post(self):
        user = self.create_user()
        problem = self.create_problem(user)

        comment = self.create_problem_comment(
            user,
            problem,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "comments:delete",
                kwargs={"pk": comment.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertTrue(
            Comment.objects.filter(
                pk=comment.pk
            ).exists()
        )


class CommentModelValidationTests(CommentTestMixin, TestCase):

    def test_comment_cannot_have_both_problem_and_solution(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(
            problem,
            user,
        )

        comment = Comment(
            user=user,
            problem=problem,
            solution=solution,
            content="Invalid comment.",
        )

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            comment.full_clean()

    def test_comment_must_have_problem_or_solution(self):
        user = self.create_user()

        comment = Comment(
            user=user,
            content="Invalid comment.",
        )

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            comment.full_clean()