from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from notifications.models import Notification
from problems.models import Problem

from .models import Solution, Vote


class SolutionTestMixin:
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

    def create_solution(self, problem, user, **kwargs):
        defaults = {
            "title": "A valid test solution",
            "description": (
                "This is a valid test solution description "
                "with enough characters."
            ),
        }

        defaults.update(kwargs)

        return Solution.objects.create(
            problem=problem,
            proposed_by=user,
            **defaults,
        )


class SolutionListTests(SolutionTestMixin, TestCase):

    def test_solution_list_is_public(self):
        response = self.client.get(
            reverse("solutions:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_solution_list_category_filter(self):
        user = self.create_user()

        campus_problem = self.create_problem(
            user,
            title="Campus problem",
            category=Problem.Category.CAMPUS,
        )

        technology_problem = self.create_problem(
            user,
            title="Technology problem",
            category=Problem.Category.TECHNOLOGY,
        )

        campus_solution = self.create_solution(
            campus_problem,
            user,
            title="Campus solution",
        )

        technology_solution = self.create_solution(
            technology_problem,
            user,
            title="Technology solution",
        )

        response = self.client.get(
            reverse("solutions:list"),
            {
                "category": Problem.Category.CAMPUS,
            },
        )

        self.assertContains(
            response,
            campus_solution.title,
        )
        self.assertNotContains(
            response,
            technology_solution.title,
        )

    def test_solution_list_status_filter(self):
        user = self.create_user()
        problem = self.create_problem(user)

        proposed_solution = self.create_solution(
            problem,
            user,
            title="Proposed solution",
            status=Solution.Status.PROPOSED,
        )

        selected_solution = self.create_solution(
            problem,
            user,
            title="Selected solution",
            status=Solution.Status.SELECTED,
        )

        response = self.client.get(
            reverse("solutions:list"),
            {
                "status": Solution.Status.SELECTED,
            },
        )

        self.assertContains(
            response,
            selected_solution.title,
        )
        self.assertNotContains(
            response,
            proposed_solution.title,
        )


class SolutionDetailTests(SolutionTestMixin, TestCase):

    def test_solution_detail_is_public(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(problem, user)

        response = self.client.get(
            reverse(
                "solutions:detail",
                kwargs={"pk": solution.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_solution_detail_shows_solution(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(
            problem,
            user,
            title="Solar powered campus buses",
        )

        response = self.client.get(
            reverse(
                "solutions:detail",
                kwargs={"pk": solution.pk},
            )
        )

        self.assertContains(
            response,
            "Solar powered campus buses",
        )


class SolutionCreateTests(SolutionTestMixin, TestCase):

    def test_anonymous_user_cannot_create_solution(self):
        response = self.client.get(
            reverse("solutions:create"),
            {"problem": 1},
        )

        self.assertRedirects(
            response,
            "/login/?next=/solutions/create/?problem=1",
        )

    def test_create_requires_problem(self):
        user = self.create_user()

        self.client.force_login(user)

        response = self.client.get(
            reverse("solutions:create")
        )

        self.assertRedirects(
            response,
            reverse("problems:list"),
        )

    def test_authenticated_user_can_create_solution(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )
        proposer = self.create_user(
            username="proposer",
            email="proposer@example.com",
        )

        problem = self.create_problem(owner)

        self.client.force_login(proposer)

        response = self.client.post(
            f"{reverse('solutions:create')}?problem={problem.pk}",
            {
                "title": "Install more water stations",
                "description": (
                    "Install additional water stations "
                    "around the campus."
                ),
            },
        )

        solution = Solution.objects.get(
            title="Install more water stations"
        )

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": solution.pk},
            ),
        )

        self.assertEqual(
            solution.proposed_by,
            proposer,
        )

        self.assertEqual(
            solution.problem,
            problem,
        )

        problem.refresh_from_db()

        self.assertEqual(
            problem.solution_count,
            1,
        )

    def test_solution_creator_is_logged_in_user(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        proposer = self.create_user(
            username="proposer",
            email="proposer@example.com",
        )

        problem = self.create_problem(owner)

        self.client.force_login(proposer)

        self.client.post(
            f"{reverse('solutions:create')}?problem={problem.pk}",
            {
                "title": "Install recycling bins",
                "description": (
                    "Install recycling bins throughout "
                    "the campus."
                ),
            },
        )

        solution = Solution.objects.get(
            title="Install recycling bins"
        )

        self.assertEqual(
            solution.proposed_by,
            proposer,
        )

    def test_solution_cannot_be_created_for_solved_problem(self):
        owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        proposer = self.create_user(
            username="proposer",
            email="proposer@example.com",
        )

        problem = self.create_problem(
            owner,
            status=Problem.Status.SOLVED,
        )

        self.client.force_login(proposer)

        response = self.client.post(
            f"{reverse('solutions:create')}?problem={problem.pk}",
            {
                "title": "New solution",
                "description": (
                    "This solution should not be accepted."
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

        self.assertFalse(
            Solution.objects.filter(
                problem=problem
            ).exists()
        )


class SolutionEditTests(SolutionTestMixin, TestCase):

    def test_owner_can_edit_solution(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(problem, user)

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "solutions:edit",
                kwargs={"pk": solution.pk},
            ),
            {
                "title": "Updated solution",
                "description": (
                    "This is an updated solution description "
                    "with enough characters."
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

        solution.refresh_from_db()

        self.assertEqual(
            solution.title,
            "Updated solution",
        )

    def test_non_owner_cannot_edit_solution(self):
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
                "solutions:edit",
                kwargs={"pk": solution.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_selected_solution_cannot_be_edited(self):
        user = self.create_user()
        problem = self.create_problem(user)

        solution = self.create_solution(
            problem,
            user,
            status=Solution.Status.SELECTED,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "solutions:edit",
                kwargs={"pk": solution.pk},
            ),
            {
                "title": "Attempted update",
                "description": (
                    "This update should not be allowed."
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

        solution.refresh_from_db()

        self.assertEqual(
            solution.title,
            "A valid test solution",
        )


class SolutionDeleteTests(SolutionTestMixin, TestCase):

    def test_owner_can_delete_solution(self):
        user = self.create_user()
        problem = self.create_problem(user)
        solution = self.create_solution(problem, user)

        problem.solution_count = 1
        problem.save(
            update_fields=["solution_count"]
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "solutions:delete",
                kwargs={"pk": solution.pk},
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
            Solution.objects.filter(
                pk=solution.pk
            ).exists()
        )

        problem.refresh_from_db()

        self.assertEqual(
            problem.solution_count,
            0,
        )

    def test_non_owner_cannot_delete_solution(self):
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

        response = self.client.post(
            reverse(
                "solutions:delete",
                kwargs={"pk": solution.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertTrue(
            Solution.objects.filter(
                pk=solution.pk
            ).exists()
        )

    def test_selected_solution_cannot_be_deleted(self):
        user = self.create_user()
        problem = self.create_problem(user)

        solution = self.create_solution(
            problem,
            user,
            status=Solution.Status.SELECTED,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "solutions:delete",
                kwargs={"pk": solution.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": solution.pk},
            ),
        )

        self.assertTrue(
            Solution.objects.filter(
                pk=solution.pk
            ).exists()
        )


class SolutionVotingTests(SolutionTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        self.voter = self.create_user(
            username="voter",
            email="voter@example.com",
        )

        self.problem = self.create_problem(
            self.owner
        )

        self.solution = self.create_solution(
            self.problem,
            self.owner,
        )

    def vote(self, vote_type):
        return self.client.post(
            reverse(
                "solutions:vote",
                kwargs={"pk": self.solution.pk},
            ),
            {
                "vote_type": vote_type,
            },
        )

    def test_vote_requires_post(self):
        self.client.force_login(self.voter)

        response = self.client.get(
            reverse(
                "solutions:vote",
                kwargs={"pk": self.solution.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_user_can_upvote_solution(self):
        self.client.force_login(self.voter)

        response = self.vote(
            Vote.VoteType.UP
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertTrue(
            data["success"]
        )

        self.assertEqual(
            data["action"],
            "added",
        )

        self.assertEqual(
            data["upvotes"],
            1,
        )

        self.assertEqual(
            data["downvotes"],
            0,
        )

        self.assertEqual(
            data["score"],
            1,
        )

        self.assertEqual(
            data["user_vote"],
            Vote.VoteType.UP,
        )

        self.solution.refresh_from_db()

        self.assertEqual(
            self.solution.upvotes,
            1,
        )

        self.assertEqual(
            self.solution.score,
            1,
        )

        self.assertTrue(
            Vote.objects.filter(
                user=self.voter,
                solution=self.solution,
                vote_type=Vote.VoteType.UP,
            ).exists()
        )

    def test_user_can_downvote_solution(self):
        self.client.force_login(self.voter)

        response = self.vote(
            Vote.VoteType.DOWN
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["downvotes"],
            1,
        )

        self.assertEqual(
            data["score"],
            -1,
        )

        self.solution.refresh_from_db()

        self.assertEqual(
            self.solution.downvotes,
            1,
        )

        self.assertEqual(
            self.solution.score,
            -1,
        )

    def test_same_vote_again_removes_vote(self):
        self.client.force_login(self.voter)

        self.vote(
            Vote.VoteType.UP
        )

        response = self.vote(
            Vote.VoteType.UP
        )

        data = response.json()

        self.assertEqual(
            data["action"],
            "removed",
        )

        self.assertEqual(
            data["upvotes"],
            0,
        )

        self.assertEqual(
            data["score"],
            0,
        )

        self.assertFalse(
            Vote.objects.filter(
                user=self.voter,
                solution=self.solution,
            ).exists()
        )

    def test_changing_vote_updates_counts(self):
        self.client.force_login(self.voter)

        self.vote(
            Vote.VoteType.UP
        )

        response = self.vote(
            Vote.VoteType.DOWN
        )

        data = response.json()

        self.assertEqual(
            data["action"],
            "changed",
        )

        self.assertEqual(
            data["upvotes"],
            0,
        )

        self.assertEqual(
            data["downvotes"],
            1,
        )

        self.assertEqual(
            data["score"],
            -1,
        )

        vote = Vote.objects.get(
            user=self.voter,
            solution=self.solution,
        )

        self.assertEqual(
            vote.vote_type,
            Vote.VoteType.DOWN,
        )

    def test_invalid_vote_type_is_rejected(self):
        self.client.force_login(self.voter)

        response = self.client.post(
            reverse(
                "solutions:vote",
                kwargs={"pk": self.solution.pk},
            ),
            {
                "vote_type": "INVALID",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        data = response.json()

        self.assertFalse(
            data["success"]
        )

    def test_user_cannot_vote_on_own_solution(self):
        self.client.force_login(self.owner)

        response = self.vote(
            Vote.VoteType.UP
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            Vote.objects.count(),
            0,
        )

    def test_upvote_creates_notification_for_solution_owner(self):
        self.client.force_login(self.voter)

        self.vote(
            Vote.VoteType.UP
        )

        notification = Notification.objects.filter(
            recipient=self.owner,
            notification_type=Notification.NotificationType.VOTE,
            related_solution=self.solution,
        ).first()

        self.assertIsNotNone(
            notification
        )

    def test_repeated_upvote_after_removal_creates_new_notification(self):
        self.client.force_login(self.voter)

        self.vote(
            Vote.VoteType.UP
        )

        self.vote(
            Vote.VoteType.UP
        )

        self.vote(
            Vote.VoteType.UP
        )

        notifications = Notification.objects.filter(
            recipient=self.owner,
            notification_type=Notification.NotificationType.VOTE,
            related_solution=self.solution,
        )

        self.assertEqual(
            notifications.count(),
            3,
        )


class SolutionSelectionTests(SolutionTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user(
            username="owner",
            email="owner@example.com",
        )

        self.author = self.create_user(
            username="author",
            email="author@example.com",
        )

        self.other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.problem = self.create_problem(
            self.owner
        )

        self.solution = self.create_solution(
            self.problem,
            self.author,
        )

    def select_solution(self):
        return self.client.post(
            reverse(
                "solutions:select",
                kwargs={"pk": self.solution.pk},
            )
        )

    def test_selection_requires_post(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "solutions:select",
                kwargs={"pk": self.solution.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_only_problem_owner_can_select_solution(self):
        self.client.force_login(self.other_user)

        response = self.select_solution()

        self.assertEqual(
            response.status_code,
            403,
        )

        self.solution.refresh_from_db()

        self.assertEqual(
            self.solution.status,
            Solution.Status.PROPOSED,
        )

    def test_problem_owner_can_select_solution(self):
        self.client.force_login(self.owner)

        response = self.select_solution()

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": self.solution.pk},
            ),
        )

        self.solution.refresh_from_db()
        self.problem.refresh_from_db()

        self.assertEqual(
            self.solution.status,
            Solution.Status.SELECTED,
        )

        self.assertEqual(
            self.problem.status,
            Problem.Status.IN_PROGRESS,
        )

    def test_selecting_new_solution_shortlists_previous_selection(self):
        second_solution = self.create_solution(
            self.problem,
            self.author,
            title="Second solution",
        )

        self.solution.status = Solution.Status.SELECTED
        self.solution.save(
            update_fields=["status"]
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "solutions:select",
                kwargs={"pk": second_solution.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": second_solution.pk},
            ),
        )

        self.solution.refresh_from_db()
        second_solution.refresh_from_db()

        self.assertEqual(
            self.solution.status,
            Solution.Status.SHORTLISTED,
        )

        self.assertEqual(
            second_solution.status,
            Solution.Status.SELECTED,
        )

    def test_rejected_solution_cannot_be_selected(self):
        self.solution.status = Solution.Status.REJECTED

        self.solution.save(
            update_fields=["status"]
        )

        self.client.force_login(self.owner)

        response = self.select_solution()

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": self.solution.pk},
            ),
        )

        self.solution.refresh_from_db()

        self.assertEqual(
            self.solution.status,
            Solution.Status.REJECTED,
        )

    def test_already_selected_solution_remains_selected(self):
        self.solution.status = Solution.Status.SELECTED

        self.solution.save(
            update_fields=["status"]
        )

        self.client.force_login(self.owner)

        response = self.select_solution()

        self.assertRedirects(
            response,
            reverse(
                "solutions:detail",
                kwargs={"pk": self.solution.pk},
            ),
        )

        self.solution.refresh_from_db()

        self.assertEqual(
            self.solution.status,
            Solution.Status.SELECTED,
        )