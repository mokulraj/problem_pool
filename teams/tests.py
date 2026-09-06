from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from problems.models import Problem
from projects.models import Project
from solutions.models import Solution

from .models import JoinRequest, TeamMembership


User = get_user_model()


class TeamsTestMixin:
    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPass123!",
        )

    def create_project(self, owner):
        problem = Problem.objects.create(
            title=f"Problem for {owner.username}",
            description="Test problem description",
            created_by=owner,
        )

        solution = Solution.objects.create(
            problem=problem,
            proposed_by=owner,
            title=f"Solution for {owner.username}",
            description="Test solution description",
        )

        return Project.objects.create(
            problem=problem,
            selected_solution=solution,
            name=f"Project {owner.username}",
            description="Test project description",
            owner=owner,
        )


class TeamMembershipModelTests(TeamsTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.project = self.create_project(self.owner)

    def test_membership_creation(self):
        membership = TeamMembership.objects.create(
            project=self.project,
            user=self.member,
            role=TeamMembership.Role.DEVELOPER,
        )

        self.assertEqual(membership.project, self.project)
        self.assertEqual(membership.user, self.member)
        self.assertEqual(
            membership.role,
            TeamMembership.Role.DEVELOPER,
        )

    def test_membership_string(self):
        membership = TeamMembership.objects.create(
            project=self.project,
            user=self.member,
            role=TeamMembership.Role.DESIGNER,
        )

        self.assertEqual(
            str(membership),
            "member - Designer - Project owner",
        )

    def test_membership_roles_are_valid(self):
        valid_roles = {
            value
            for value, label in TeamMembership.Role.choices
        }

        self.assertIn(
            TeamMembership.Role.PROJECT_MANAGER,
            valid_roles,
        )
        self.assertIn(
            TeamMembership.Role.DEVELOPER,
            valid_roles,
        )
        self.assertIn(
            TeamMembership.Role.DESIGNER,
            valid_roles,
        )
        self.assertIn(
            TeamMembership.Role.RESEARCHER,
            valid_roles,
        )
        self.assertIn(
            TeamMembership.Role.TESTER,
            valid_roles,
        )
        self.assertIn(
            TeamMembership.Role.OTHER,
            valid_roles,
        )

    def test_duplicate_membership_is_rejected(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        with self.assertRaises(Exception):
            TeamMembership.objects.create(
                project=self.project,
                user=self.member,
            )


class JoinRequestModelTests(TeamsTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.project = self.create_project(self.owner)

    def test_join_request_creation(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
            message="I would like to join.",
        )

        self.assertEqual(
            join_request.status,
            JoinRequest.Status.PENDING,
        )
        self.assertEqual(join_request.project, self.project)
        self.assertEqual(join_request.user, self.member)

    def test_project_owner_cannot_request_to_join(self):
        join_request = JoinRequest(
            project=self.project,
            user=self.owner,
        )

        with self.assertRaises(ValidationError):
            join_request.full_clean()

    def test_existing_member_cannot_request_to_join(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        join_request = JoinRequest(
            project=self.project,
            user=self.member,
        )

        with self.assertRaises(ValidationError):
            join_request.full_clean()

    def test_join_request_string(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.assertEqual(
            str(join_request),
            "member → Project owner",
        )


class TeamViewTests(TeamsTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.other_user = self.create_user("other")
        self.project = self.create_project(self.owner)

    def test_join_requires_login(self):
        response = self.client.get(
            reverse(
                "teams:join",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_join_get_shows_form(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "teams:join",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "teams/join_request_form.html",
        )

    def test_join_creates_request(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "teams:join",
                kwargs={"project_id": self.project.pk},
            ),
            {"message": "I want to help with this project."},
        )

        self.assertEqual(response.status_code, 302)

        join_request = JoinRequest.objects.get(
            project=self.project,
            user=self.member,
        )

        self.assertEqual(
            join_request.status,
            JoinRequest.Status.PENDING,
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.owner,
                related_project=self.project,
                notification_type=(
                    Notification.NotificationType.JOIN_REQUEST
                ),
            ).exists()
        )

    def test_owner_cannot_join_own_project(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "teams:join",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            JoinRequest.objects.filter(
                project=self.project,
                user=self.owner,
            ).exists()
        )

    def test_existing_member_cannot_create_request(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "teams:join",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            JoinRequest.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

    def test_duplicate_pending_request_is_blocked(self):
        JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "teams:join",
                kwargs={"project_id": self.project.pk},
            ),
            {"message": "Another request."},
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            JoinRequest.objects.filter(
                project=self.project,
                user=self.member,
                status=JoinRequest.Status.PENDING,
            ).count(),
            1,
        )

    def test_join_request_list_requires_owner(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "teams:join_requests",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_join_request_list_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "teams:join_requests",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "teams/join_requests.html",
        )

    def test_approve_request(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "teams:approve",
                kwargs={"request_id": join_request.pk},
            ),
            {
                "role": TeamMembership.Role.DEVELOPER,
            },
        )

        self.assertEqual(response.status_code, 302)

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            JoinRequest.Status.APPROVED,
        )

        membership = TeamMembership.objects.get(
            project=self.project,
            user=self.member,
        )

        self.assertEqual(
            membership.role,
            TeamMembership.Role.DEVELOPER,
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.member,
                related_project=self.project,
                notification_type=(
                    Notification.NotificationType.JOIN_APPROVED
                ),
            ).exists()
        )

    def test_approve_requires_post(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "teams:approve",
                kwargs={"request_id": join_request.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            JoinRequest.Status.PENDING,
        )

    def test_non_owner_cannot_approve(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "teams:approve",
                kwargs={"request_id": join_request.pk},
            ),
            {
                "role": TeamMembership.Role.DEVELOPER,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_invalid_role_cannot_approve(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "teams:approve",
                kwargs={"request_id": join_request.pk},
            ),
            {"role": "INVALID_ROLE"},
        )

        self.assertEqual(response.status_code, 302)

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            JoinRequest.Status.PENDING,
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

    def test_reject_request(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "teams:reject",
                kwargs={"request_id": join_request.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            JoinRequest.Status.REJECTED,
        )

    def test_reject_requires_post(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "teams:reject",
                kwargs={"request_id": join_request.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_non_owner_cannot_reject(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "teams:reject",
                kwargs={"request_id": join_request.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_cancel_request(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "teams:cancel",
                kwargs={"request_id": join_request.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            JoinRequest.objects.filter(
                pk=join_request.pk,
            ).exists()
        )

    def test_cancel_requires_post(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "teams:cancel",
                kwargs={"request_id": join_request.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            JoinRequest.objects.filter(
                pk=join_request.pk,
            ).exists()
        )

    def test_other_user_cannot_cancel_request(self):
        join_request = JoinRequest.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "teams:cancel",
                kwargs={"request_id": join_request.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            JoinRequest.objects.filter(
                pk=join_request.pk,
            ).exists()
        )

    def test_change_member_role(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
            role=TeamMembership.Role.DEVELOPER,
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "teams:change_member_role",
                kwargs={
                    "project_id": self.project.pk,
                    "user_id": self.member.pk,
                },
            ),
            {
                "role": TeamMembership.Role.DESIGNER,
            },
        )

        self.assertEqual(response.status_code, 302)

        membership = TeamMembership.objects.get(
            project=self.project,
            user=self.member,
        )

        self.assertEqual(
            membership.role,
            TeamMembership.Role.DESIGNER,
        )

    def test_change_role_requires_post(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "teams:change_member_role",
                kwargs={
                    "project_id": self.project.pk,
                    "user_id": self.member.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_non_owner_cannot_change_role(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "teams:change_member_role",
                kwargs={
                    "project_id": self.project.pk,
                    "user_id": self.member.pk,
                },
            ),
            {
                "role": TeamMembership.Role.DESIGNER,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_invalid_role_cannot_be_assigned(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
            role=TeamMembership.Role.DEVELOPER,
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "teams:change_member_role",
                kwargs={
                    "project_id": self.project.pk,
                    "user_id": self.member.pk,
                },
            ),
            {
                "role": "INVALID_ROLE",
            },
        )

        self.assertEqual(response.status_code, 302)

        membership = TeamMembership.objects.get(
            project=self.project,
            user=self.member,
        )

        self.assertEqual(
            membership.role,
            TeamMembership.Role.DEVELOPER,
        )

    def test_remove_member(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "teams:remove_member",
                kwargs={
                    "project_id": self.project.pk,
                    "user_id": self.member.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            TeamMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.member,
                related_project=self.project,
                notification_type=(
                    Notification.NotificationType.JOIN_REQUEST
                ),
            ).exists()
        )

    def test_remove_member_requires_post(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "teams:remove_member",
                kwargs={
                    "project_id": self.project.pk,
                    "user_id": self.member.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            TeamMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

    def test_non_owner_cannot_remove_member(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "teams:remove_member",
                kwargs={
                    "project_id": self.project.pk,
                    "user_id": self.member.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            TeamMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

    def test_member_can_leave_project(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "teams:leave",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            TeamMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

    def test_leave_requires_post(self):
        TeamMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "teams:leave",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            TeamMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

    def test_owner_cannot_leave_project(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "teams:leave",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Project.objects.filter(
                pk=self.project.pk,
                owner=self.owner,
            ).exists()
        )

    def test_non_member_cannot_leave_project(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "teams:leave",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            TeamMembership.objects.filter(
                project=self.project,
                user=self.other_user,
            ).exists()
        )