from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from problems.models import Problem
from projects.models import Project
from solutions.models import Solution
from teams.models import TeamMembership

from .models import Task


User = get_user_model()


class TasksTestMixin:

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

    def add_member(self, project, user, role=TeamMembership.Role.DEVELOPER):
        return TeamMembership.objects.create(
            project=project,
            user=user,
            role=role,
        )


class TaskModelTests(TasksTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.other_user = self.create_user("other")
        self.project = self.create_project(self.owner)

        self.add_member(
            self.project,
            self.member,
            TeamMembership.Role.DEVELOPER,
        )

        self.add_member(
            self.project,
            self.other_user,
            TeamMembership.Role.DEVELOPER,
        )

    def test_task_creation(self):
        task = Task.objects.create(
            project=self.project,
            title="Build feature",
            description="Build the requested feature.",
        )

        self.assertEqual(task.project, self.project)
        self.assertEqual(task.title, "Build feature")
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertIsNone(task.assigned_to)

    def test_task_string(self):
        task = Task.objects.create(
            project=self.project,
            title="Build feature",
        )

        self.assertEqual(
            str(task),
            "Build feature",
        )

    def test_task_status_choices(self):
        statuses = {
            value
            for value, label in Task.Status.choices
        }

        self.assertIn(Task.Status.TODO, statuses)
        self.assertIn(Task.Status.IN_PROGRESS, statuses)
        self.assertIn(Task.Status.COMPLETED, statuses)

    def test_due_date_before_project_deadline_is_valid(self):
        self.project.end_date = date(2026, 12, 31)
        self.project.save(update_fields=["end_date"])

        task = Task(
            project=self.project,
            title="Valid task",
            due_date=date(2026, 12, 30),
        )

        task.full_clean()

    def test_due_date_equal_to_project_deadline_is_valid(self):
        self.project.end_date = date(2026, 12, 31)
        self.project.save(update_fields=["end_date"])

        task = Task(
            project=self.project,
            title="Deadline task",
            due_date=date(2026, 12, 31),
        )

        task.full_clean()

    def test_due_date_after_project_deadline_is_rejected(self):
        self.project.end_date = date(2026, 12, 31)
        self.project.save(update_fields=["end_date"])

        task = Task(
            project=self.project,
            title="Late task",
            due_date=date(2027, 1, 1),
        )

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_due_date_without_project_deadline_is_allowed(self):
        task = Task(
            project=self.project,
            title="No deadline task",
            due_date=date(2030, 1, 1),
        )

        task.full_clean()


class TaskListViewTests(TasksTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.other_user = self.create_user("other")
        self.project = self.create_project(self.owner)

        self.add_member(
            self.project,
            self.member,
        )

    def test_task_list_requires_login(self):
        response = self.client.get(
            reverse(
                "tasks:list",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_project_owner_can_view_task_list(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "tasks:list",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "tasks/task_list.html",
        )

    def test_project_member_can_view_task_list(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "tasks:list",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_non_member_cannot_view_task_list(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "tasks:list",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 403)


class TaskCreateViewTests(TasksTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.other_user = self.create_user("other")
        self.project = self.create_project(self.owner)

        self.add_member(
            self.project,
            self.member,
        )

        self.add_member(
            self.project,
            self.other_user,
        )

    def test_task_create_requires_login(self):
        response = self.client.get(
            reverse(
                "tasks:create",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_owner_can_open_task_create_form(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "tasks:create",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "tasks/task_form.html",
        )

    def test_non_owner_cannot_create_task(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "tasks:create",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_task(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:create",
                kwargs={"project_id": self.project.pk},
            ),
            {
                "title": "New task",
                "description": "Task description",
                "assigned_to": "",
                "due_date": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        task = Task.objects.get(
            project=self.project,
            title="New task",
        )

        self.assertEqual(
            task.status,
            Task.Status.TODO,
        )

    def test_task_can_be_assigned_on_creation(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:create",
                kwargs={"project_id": self.project.pk},
            ),
            {
                "title": "Assigned task",
                "description": "Assigned task description",
                "assigned_to": self.member.pk,
                "due_date": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        task = Task.objects.get(
            project=self.project,
            title="Assigned task",
        )

        self.assertEqual(
            task.assigned_to,
            self.member,
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.member,
                related_project=self.project,
                notification_type=(
                    Notification.NotificationType.TASK_ASSIGNED
                ),
            ).exists()
        )


class TaskEditViewTests(TasksTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.other_user = self.create_user("other")
        self.project = self.create_project(self.owner)

        self.add_member(
            self.project,
            self.member,
        )

        self.add_member(
            self.project,
            self.other_user,
            TeamMembership.Role.DESIGNER,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Original task",
            description="Original description",
            assigned_to=self.member,
            status=Task.Status.IN_PROGRESS,
        )

    def test_owner_can_open_edit_form(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "tasks:edit",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "tasks/task_form.html",
        )

    def test_non_owner_cannot_edit_task(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "tasks:edit",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_edit_task(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:edit",
                kwargs={"pk": self.task.pk},
            ),
            {
                "title": "Updated task",
                "description": "Updated description",
                "assigned_to": self.member.pk,
                "due_date": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.title,
            "Updated task",
        )

        self.assertEqual(
            self.task.description,
            "Updated description",
        )

    def test_edit_preserves_existing_status(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:edit",
                kwargs={"pk": self.task.pk},
            ),
            {
                "title": "Updated task",
                "description": "Updated description",
                "assigned_to": self.member.pk,
                "due_date": "",
                "status": Task.Status.COMPLETED,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.IN_PROGRESS,
        )

    def test_changing_assignee_creates_notification(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:edit",
                kwargs={"pk": self.task.pk},
            ),
            {
                "title": "Reassigned task",
                "description": "Updated description",
                "assigned_to": self.other_user.pk,
                "due_date": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.other_user,
                related_project=self.project,
                notification_type=(
                    Notification.NotificationType.TASK_ASSIGNED
                ),
            ).exists()
        )


class TaskDeleteViewTests(TasksTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.project = self.create_project(self.owner)

        self.add_member(
            self.project,
            self.member,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Delete me",
        )

    def test_non_owner_cannot_delete_task(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:delete",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Task.objects.filter(pk=self.task.pk).exists()
        )

    def test_delete_requires_post(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "tasks:delete",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Task.objects.filter(pk=self.task.pk).exists()
        )

    def test_owner_can_delete_task(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:delete",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Task.objects.filter(pk=self.task.pk).exists()
        )


class TaskStatusViewTests(TasksTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.other_user = self.create_user("other")
        self.project = self.create_project(self.owner)

        self.add_member(
            self.project,
            self.member,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Status task",
            assigned_to=self.member,
            status=Task.Status.TODO,
        )

    def test_only_assigned_member_can_update_status(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            ),
            {
                "status": Task.Status.IN_PROGRESS,
            },
        )

        self.assertEqual(response.status_code, 403)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    def test_project_owner_cannot_update_assigned_task_status(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            ),
            {
                "status": Task.Status.IN_PROGRESS,
            },
        )

        self.assertEqual(response.status_code, 403)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    def test_status_update_requires_post(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    def test_assigned_member_can_update_status(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            ),
            {
                "status": Task.Status.IN_PROGRESS,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.IN_PROGRESS,
        )

    def test_invalid_status_is_rejected(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            ),
            {
                "status": "INVALID_STATUS",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    def test_same_status_does_not_change_task(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            ),
            {
                "status": Task.Status.TODO,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    @patch("tasks.views.award_points")
    def test_completing_task_awards_points(self, mock_award_points):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            ),
            {
                "status": Task.Status.COMPLETED,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.COMPLETED,
        )

        mock_award_points.assert_called_once_with(
            self.member,
            "TASK_COMPLETED",
            self.task.pk,
        )

    def test_status_update_notifies_project_owner(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:status_update",
                kwargs={"pk": self.task.pk},
            ),
            {
                "status": Task.Status.IN_PROGRESS,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.owner,
                related_project=self.project,
                notification_type=(
                    Notification.NotificationType.TASK_ASSIGNED
                ),
            ).exists()
        )


class TaskCompleteViewTests(TasksTestMixin, TestCase):

    def setUp(self):
        self.owner = self.create_user("owner")
        self.member = self.create_user("member")
        self.other_user = self.create_user("other")
        self.project = self.create_project(self.owner)

        self.add_member(
            self.project,
            self.member,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Complete task",
            assigned_to=self.member,
            status=Task.Status.TODO,
        )

    def test_complete_requires_post(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "tasks:complete",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    def test_only_assigned_member_can_complete(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "tasks:complete",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    @patch("tasks.views.award_points")
    def test_assigned_member_can_complete_task(self, mock_award_points):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:complete",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.COMPLETED,
        )

        mock_award_points.assert_called_once_with(
            self.member,
            "TASK_COMPLETED",
            self.task.pk,
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.owner,
                related_project=self.project,
                notification_type=(
                    Notification.NotificationType.TASK_ASSIGNED
                ),
            ).exists()
        )

    @patch("tasks.views.award_points")
    def test_already_completed_task_does_not_award_again(
        self,
        mock_award_points,
    ):
        self.task.status = Task.Status.COMPLETED
        self.task.save(update_fields=["status"])

        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:complete",
                kwargs={"pk": self.task.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        mock_award_points.assert_not_called()