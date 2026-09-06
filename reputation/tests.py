from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from problems.models import Problem
from solutions.models import Solution

from .models import ReputationReward
from .services import REWARD_POINTS, award_points


User = get_user_model()


class ReputationTestMixin:

    def create_user(self, username, points=0, is_active=True):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPass123!",
            points=points,
            is_active=is_active,
        )

    def create_problem(self, user, title="Test Problem"):
        return Problem.objects.create(
            title=title,
            description="Test problem description.",
            created_by=user,
        )

    def create_solution(self, problem, user, title="Test Solution"):
        return Solution.objects.create(
            problem=problem,
            proposed_by=user,
            title=title,
            description="Test solution description.",
        )

    def create_project(self, owner, problem=None, solution=None):
        if problem is None:
            problem = self.create_problem(owner)

        if solution is None:
            solution = self.create_solution(
                problem,
                owner,
            )

        return Project.objects.create(
            problem=problem,
            selected_solution=solution,
            name="Test Project",
            description="Test project description.",
            owner=owner,
        )


class ReputationRewardModelTests(
    ReputationTestMixin,
    TestCase,
):

    def setUp(self):
        self.user = self.create_user("user")

    def test_reward_creation(self):
        reward = ReputationReward.objects.create(
            user=self.user,
            reward_type=(
                ReputationReward.RewardType.PROBLEM_CREATED
            ),
            points=5,
            reference_id=100,
        )

        self.assertEqual(
            str(reward),
            "user - Problem Created - 5 points",
        )

        self.assertEqual(
            reward.reward_type,
            ReputationReward.RewardType.PROBLEM_CREATED,
        )

        self.assertEqual(
            reward.points,
            5,
        )

        self.assertEqual(
            reward.reference_id,
            100,
        )

    def test_reward_string(self):
        reward = ReputationReward.objects.create(
            user=self.user,
            reward_type=(
                ReputationReward.RewardType.PROBLEM_CREATED
            ),
            points=5,
            reference_id=100,
        )

        self.assertEqual(
            str(reward),
            "user - Problem Created - 5 points",
        )

    def test_reward_reference_id_can_be_null(self):
        reward = ReputationReward.objects.create(
            user=self.user,
            reward_type=(
                ReputationReward.RewardType.SOLUTION_PROPOSED
            ),
            points=10,
        )

        self.assertIsNone(
            reward.reference_id,
        )

    def test_reward_type_choices_exist(self):
        reward_types = {
            value
            for value, label in ReputationReward.RewardType.choices
        }

        self.assertIn(
            ReputationReward.RewardType.PROBLEM_CREATED,
            reward_types,
        )

        self.assertIn(
            ReputationReward.RewardType.SOLUTION_PROPOSED,
            reward_types,
        )

        self.assertIn(
            ReputationReward.RewardType.UPVOTE_RECEIVED,
            reward_types,
        )

        self.assertIn(
            ReputationReward.RewardType.SOLUTION_SELECTED,
            reward_types,
        )

        self.assertIn(
            ReputationReward.RewardType.TASK_COMPLETED,
            reward_types,
        )

        self.assertIn(
            ReputationReward.RewardType.PROJECT_COMPLETED,
            reward_types,
        )

    def test_unique_user_reward_reference_constraint(self):
        ReputationReward.objects.create(
            user=self.user,
            reward_type=(
                ReputationReward.RewardType.PROBLEM_CREATED
            ),
            points=5,
            reference_id=100,
        )

        with self.assertRaises(Exception):
            ReputationReward.objects.create(
                user=self.user,
                reward_type=(
                    ReputationReward.RewardType.PROBLEM_CREATED
                ),
                points=5,
                reference_id=100,
            )

    def test_same_reward_type_can_use_different_reference_ids(self):
        first_reward = ReputationReward.objects.create(
            user=self.user,
            reward_type=(
                ReputationReward.RewardType.PROBLEM_CREATED
            ),
            points=5,
            reference_id=100,
        )

        second_reward = ReputationReward.objects.create(
            user=self.user,
            reward_type=(
                ReputationReward.RewardType.PROBLEM_CREATED
            ),
            points=5,
            reference_id=101,
        )

        self.assertNotEqual(
            first_reward.pk,
            second_reward.pk,
        )

    def test_different_users_can_receive_same_reward_reference(self):
        other_user = self.create_user("other")

        first_reward = ReputationReward.objects.create(
            user=self.user,
            reward_type=(
                ReputationReward.RewardType.PROBLEM_CREATED
            ),
            points=5,
            reference_id=100,
        )

        second_reward = ReputationReward.objects.create(
            user=other_user,
            reward_type=(
                ReputationReward.RewardType.PROBLEM_CREATED
            ),
            points=5,
            reference_id=100,
        )

        self.assertNotEqual(
            first_reward.user,
            second_reward.user,
        )


class AwardPointsTests(
    ReputationTestMixin,
    TestCase,
):

    def setUp(self):
        self.user = self.create_user(
            "user",
            points=0,
        )

    def test_reward_point_values(self):
        self.assertEqual(
            REWARD_POINTS[
                ReputationReward.RewardType.PROBLEM_CREATED
            ],
            5,
        )

        self.assertEqual(
            REWARD_POINTS[
                ReputationReward.RewardType.SOLUTION_PROPOSED
            ],
            10,
        )

        self.assertEqual(
            REWARD_POINTS[
                ReputationReward.RewardType.UPVOTE_RECEIVED
            ],
            2,
        )

        self.assertEqual(
            REWARD_POINTS[
                ReputationReward.RewardType.SOLUTION_SELECTED
            ],
            25,
        )

        self.assertEqual(
            REWARD_POINTS[
                ReputationReward.RewardType.TASK_COMPLETED
            ],
            5,
        )

        self.assertEqual(
            REWARD_POINTS[
                ReputationReward.RewardType.PROJECT_COMPLETED
            ],
            50,
        )

    def test_award_points_creates_reward(self):
        reward, created = award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            100,
        )

        self.assertTrue(created)

        self.assertEqual(
            reward.user,
            self.user,
        )

        self.assertEqual(
            reward.reward_type,
            ReputationReward.RewardType.PROBLEM_CREATED,
        )

        self.assertEqual(
            reward.points,
            5,
        )

        self.assertEqual(
            reward.reference_id,
            100,
        )

    def test_award_points_increases_user_points(self):
        self.assertEqual(
            self.user.points,
            0,
        )

        award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            100,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            5,
        )

    def test_award_points_returns_created_true_first_time(self):
        reward, created = award_points(
            self.user,
            ReputationReward.RewardType.SOLUTION_PROPOSED,
            200,
        )

        self.assertTrue(created)
        self.assertEqual(reward.points, 10)

    def test_duplicate_reward_does_not_award_points_again(self):
        award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            100,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            5,
        )

        reward, created = award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            100,
        )

        self.assertFalse(created)

        self.assertEqual(
            reward.points,
            5,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            5,
        )

        self.assertEqual(
            ReputationReward.objects.filter(
                user=self.user,
                reward_type=(
                    ReputationReward.RewardType.PROBLEM_CREATED
                ),
                reference_id=100,
            ).count(),
            1,
        )

    def test_different_references_award_points_separately(self):
        award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            100,
        )

        award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            101,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            10,
        )

        self.assertEqual(
            ReputationReward.objects.filter(
                user=self.user,
                reward_type=(
                    ReputationReward.RewardType.PROBLEM_CREATED
                ),
            ).count(),
            2,
        )

    def test_different_reward_types_award_points_separately(self):
        award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            100,
        )

        award_points(
            self.user,
            ReputationReward.RewardType.SOLUTION_PROPOSED,
            200,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            15,
        )

    def test_existing_user_points_are_preserved(self):
        self.user.points = 20
        self.user.save(update_fields=["points"])

        award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
            100,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            25,
        )

    def test_invalid_reward_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            award_points(
                self.user,
                "INVALID_REWARD_TYPE",
                100,
            )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            0,
        )

        self.assertEqual(
            ReputationReward.objects.count(),
            0,
        )

    def test_reward_without_reference_id_is_awarded(self):
        reward, created = award_points(
            self.user,
            ReputationReward.RewardType.PROBLEM_CREATED,
        )

        self.assertTrue(created)

        self.assertIsNone(
            reward.reference_id,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            5,
        )


class LeaderboardViewTests(
    ReputationTestMixin,
    TestCase,
):

    def setUp(self):
        self.current_user = self.create_user(
            "current",
            points=20,
        )

    def test_leaderboard_requires_login(self):
        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_can_view_leaderboard(self):
        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "reputation/leaderboard.html",
        )

    def test_leaderboard_orders_users_by_points_descending(self):
        first = self.create_user(
            "first",
            points=100,
        )

        second = self.create_user(
            "second",
            points=50,
        )

        third = self.create_user(
            "third",
            points=10,
        )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        top_users = list(
            response.context["top_users"]
        )

        self.assertEqual(
            top_users[0],
            first,
        )

        self.assertEqual(
            top_users[1],
            second,
        )

        self.assertEqual(
            top_users[2],
            self.current_user,
        )

        self.assertEqual(
            top_users[3],
            third,
        )

    def test_leaderboard_uses_username_as_tiebreaker(self):
        user_b = self.create_user(
            "bravo",
            points=50,
        )

        user_a = self.create_user(
            "alpha",
            points=50,
        )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        top_users = list(
            response.context["top_users"]
        )

        self.assertLess(
            top_users.index(user_a),
            top_users.index(user_b),
        )

    def test_leaderboard_excludes_inactive_users(self):
        inactive = self.create_user(
            "inactive",
            points=1000,
            is_active=False,
        )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        top_users = list(
            response.context["top_users"]
        )

        self.assertNotIn(
            inactive,
            top_users,
        )

    def test_leaderboard_returns_at_most_ten_users(self):
        for index in range(15):
            self.create_user(
                f"user{index:02d}",
                points=100 - index,
            )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        top_users = response.context["top_users"]

        self.assertLessEqual(
            len(top_users),
            10,
        )

    def test_leaderboard_assigns_rank_numbers(self):
        first = self.create_user(
            "first",
            points=100,
        )

        second = self.create_user(
            "second",
            points=50,
        )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        top_users = list(
            response.context["top_users"]
        )

        self.assertEqual(
            top_users[0],
            first,
        )

        self.assertEqual(
            top_users[0].leaderboard_rank,
            1,
        )

        self.assertEqual(
            top_users[1],
            second,
        )

        self.assertEqual(
            top_users[1].leaderboard_rank,
            2,
        )

    def test_current_user_position_is_calculated(self):
        self.create_user(
            "first",
            points=100,
        )

        self.create_user(
            "second",
            points=50,
        )

        self.create_user(
            "third",
            points=30,
        )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        self.assertEqual(
            response.context["current_user_position"],
            4,
        )

    def test_current_user_position_is_first_when_highest(self):
        self.current_user.points = 500
        self.current_user.save(
            update_fields=["points"]
        )

        self.create_user(
            "lower",
            points=100,
        )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        self.assertEqual(
            response.context["current_user_position"],
            1,
        )

    def test_current_user_position_is_one_based(self):
        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        self.assertEqual(
            response.context["current_user_position"],
            1,
        )

    def test_leaderboard_context_contains_current_user(self):
        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        self.assertEqual(
            response.context["current_user"],
            self.current_user,
        )

    def test_leaderboard_context_contains_expected_keys(self):
        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        self.assertIn(
            "top_users",
            response.context,
        )

        self.assertIn(
            "current_user_position",
            response.context,
        )

        self.assertIn(
            "current_user",
            response.context,
        )

    def test_leaderboard_includes_user_statistics(self):
        problem = self.create_problem(
            self.current_user,
            title="Statistics Problem",
        )

        solution = self.create_solution(
            problem,
            self.current_user,
            title="Statistics Solution",
        )

        self.create_project(
            self.current_user,
            problem=problem,
            solution=solution,
        )

        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("reputation:leaderboard")
        )

        user = next(
            user
            for user in response.context["top_users"]
            if user.pk == self.current_user.pk
        )

        self.assertEqual(
            user.problems_created_count,
            1,
        )

        self.assertEqual(
            user.solutions_submitted_count,
            1,
        )

        self.assertEqual(
            user.projects_owned_count,
            1,
        )

        self.assertEqual(
            user.projects_completed_count,
            0,
        )