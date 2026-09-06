from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from problems.models import Problem
from projects.models import Project
from solutions.models import Solution


User = get_user_model()


class NotificationTestMixin:

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPass123!",
        )

    def create_problem(self, user, title="Test Problem"):
        return Problem.objects.create(
            title=title,
            description="Test problem description.",
            created_by=user,
        )

    def create_solution(self, problem, user):
        return Solution.objects.create(
            problem=problem,
            proposed_by=user,
            title="Test Solution",
            description="Test solution description.",
        )

    def create_project(self, user, problem=None, solution=None):
        if problem is None:
            problem = self.create_problem(user)

        if solution is None:
            solution = self.create_solution(
                problem,
                user,
            )

        return Project.objects.create(
            problem=problem,
            selected_solution=solution,
            name="Test Project",
            description="Test project description.",
            owner=user,
        )

    def create_notification(
        self,
        recipient,
        notification_type=Notification.NotificationType.COMMENT,
        message="Test notification",
        problem=None,
        solution=None,
        project=None,
        is_read=False,
    ):
        return Notification.objects.create(
            recipient=recipient,
            message=message,
            notification_type=notification_type,
            related_problem=problem,
            related_solution=solution,
            related_project=project,
            is_read=is_read,
        )


class NotificationModelTests(NotificationTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("user")

    def test_notification_creation(self):
        notification = self.create_notification(
            recipient=self.user,
            message="A new comment was added.",
        )

        self.assertEqual(
            notification.recipient,
            self.user,
        )

        self.assertEqual(
            notification.message,
            "A new comment was added.",
        )

        self.assertFalse(
            notification.is_read,
        )

    def test_notification_string(self):
        notification = self.create_notification(
            recipient=self.user,
            message="You have a notification.",
        )

        self.assertEqual(
            str(notification),
            "user: You have a notification.",
        )

    def test_notification_is_unread_by_default(self):
        notification = self.create_notification(
            recipient=self.user,
        )

        self.assertFalse(
            notification.is_read,
        )

    def test_notification_can_be_marked_read(self):
        notification = self.create_notification(
            recipient=self.user,
        )

        notification.is_read = True
        notification.save(
            update_fields=["is_read"]
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read,
        )

    def test_notification_types_exist(self):
        notification_types = {
            value
            for value, label in Notification.NotificationType.choices
        }

        self.assertIn(
            Notification.NotificationType.SOLUTION_PROPOSED,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.COMMENT,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.VOTE,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.SOLUTION_SELECTED,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.JOIN_REQUEST,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.JOIN_APPROVED,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.TASK_ASSIGNED,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.TASK_STATUS_UPDATED,
            notification_types,
        )

        self.assertIn(
            Notification.NotificationType.PROJECT_COMPLETED,
            notification_types,
        )


class NotificationListViewTests(
    NotificationTestMixin,
    TestCase,
):

    def setUp(self):
        self.user = self.create_user("user")
        self.other_user = self.create_user("other")

        self.problem = self.create_problem(
            self.user,
            title="Problem Notification",
        )

        self.solution = self.create_solution(
            self.problem,
            self.user,
        )

        self.project = self.create_project(
            self.user,
            problem=self.problem,
            solution=self.solution,
        )

    def test_notification_list_requires_login(self):
        response = self.client.get(
            reverse("notifications:list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_can_view_notification_list(self):
        self.client.force_login(self.user)

        self.create_notification(
            recipient=self.user,
            message="Hello user.",
        )

        response = self.client.get(
            reverse("notifications:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "notifications/notification_list.html",
        )

        self.assertContains(
            response,
            "Hello user.",
        )

    def test_user_only_sees_own_notifications(self):
        self.client.force_login(self.user)

        self.create_notification(
            recipient=self.user,
            message="Own notification.",
        )

        self.create_notification(
            recipient=self.other_user,
            message="Other notification.",
        )

        response = self.client.get(
            reverse("notifications:list")
        )

        self.assertContains(
            response,
            "Own notification.",
        )

        self.assertNotContains(
            response,
            "Other notification.",
        )

    def test_all_filter_is_default(self):
        self.client.force_login(self.user)

        notification = self.create_notification(
            recipient=self.user,
            message="All notification.",
        )

        response = self.client.get(
            reverse("notifications:list")
        )

        self.assertEqual(
            response.context["active_filter"],
            "all",
        )

        self.assertContains(
            response,
            notification.message,
        )

    def test_unread_filter(self):
        self.client.force_login(self.user)

        unread = self.create_notification(
            recipient=self.user,
            message="Unread notification.",
            is_read=False,
        )

        read = self.create_notification(
            recipient=self.user,
            message="Read notification.",
            is_read=True,
        )

        response = self.client.get(
            reverse("notifications:list"),
            {"filter": "unread"},
        )

        self.assertEqual(
            response.context["active_filter"],
            "unread",
        )

        self.assertContains(
            response,
            unread.message,
        )

        self.assertNotContains(
            response,
            read.message,
        )

    def test_problem_filter(self):
        self.client.force_login(self.user)

        problem_notification = self.create_notification(
            recipient=self.user,
            message="Problem notification.",
            problem=self.problem,
        )

        system_notification = self.create_notification(
            recipient=self.user,
            message="System notification.",
        )

        response = self.client.get(
            reverse("notifications:list"),
            {"filter": "problems"},
        )

        self.assertEqual(
            response.context["active_filter"],
            "problems",
        )

        self.assertContains(
            response,
            problem_notification.message,
        )

        self.assertNotContains(
            response,
            system_notification.message,
        )

    def test_solution_filter(self):
        self.client.force_login(self.user)

        solution_notification = self.create_notification(
            recipient=self.user,
            message="Solution notification.",
            solution=self.solution,
        )

        system_notification = self.create_notification(
            recipient=self.user,
            message="System notification.",
        )

        response = self.client.get(
            reverse("notifications:list"),
            {"filter": "solutions"},
        )

        self.assertEqual(
            response.context["active_filter"],
            "solutions",
        )

        self.assertContains(
            response,
            solution_notification.message,
        )

        self.assertNotContains(
            response,
            system_notification.message,
        )

    def test_project_filter(self):
        self.client.force_login(self.user)

        project_notification = self.create_notification(
            recipient=self.user,
            message="Project notification.",
            project=self.project,
        )

        system_notification = self.create_notification(
            recipient=self.user,
            message="System notification.",
        )

        response = self.client.get(
            reverse("notifications:list"),
            {"filter": "projects"},
        )

        self.assertEqual(
            response.context["active_filter"],
            "projects",
        )

        self.assertContains(
            response,
            project_notification.message,
        )

        self.assertNotContains(
            response,
            system_notification.message,
        )

    def test_system_filter(self):
        self.client.force_login(self.user)

        system_notification = self.create_notification(
            recipient=self.user,
            message="System notification.",
        )

        problem_notification = self.create_notification(
            recipient=self.user,
            message="Problem notification.",
            problem=self.problem,
        )

        response = self.client.get(
            reverse("notifications:list"),
            {"filter": "system"},
        )

        self.assertEqual(
            response.context["active_filter"],
            "system",
        )

        self.assertContains(
            response,
            system_notification.message,
        )

        self.assertNotContains(
            response,
            problem_notification.message,
        )

    def test_notification_counts(self):
        self.client.force_login(self.user)

        self.create_notification(
            recipient=self.user,
            message="Unread problem.",
            problem=self.problem,
            is_read=False,
        )

        self.create_notification(
            recipient=self.user,
            message="Read solution.",
            solution=self.solution,
            is_read=True,
        )

        self.create_notification(
            recipient=self.user,
            message="Unread project.",
            project=self.project,
            is_read=False,
        )

        self.create_notification(
            recipient=self.user,
            message="System notification.",
            is_read=False,
        )

        response = self.client.get(
            reverse("notifications:list")
        )

        self.assertEqual(
            response.context["unread_count"],
            3,
        )

        self.assertEqual(
            response.context["problem_count"],
            1,
        )

        self.assertEqual(
            response.context["solution_count"],
            1,
        )

        self.assertEqual(
            response.context["project_count"],
            1,
        )

        self.assertEqual(
            response.context["system_count"],
            1,
        )

    def test_counts_only_include_current_users_notifications(self):
        self.client.force_login(self.user)

        self.create_notification(
            recipient=self.user,
            message="My notification.",
            problem=self.problem,
        )

        self.create_notification(
            recipient=self.other_user,
            message="Other notification.",
            problem=self.problem,
        )

        response = self.client.get(
            reverse("notifications:list")
        )

        self.assertEqual(
            response.context["problem_count"],
            1,
        )


class MarkNotificationReadTests(
    NotificationTestMixin,
    TestCase,
):

    def setUp(self):
        self.user = self.create_user("user")
        self.other_user = self.create_user("other")

        self.notification = self.create_notification(
            recipient=self.user,
            message="Unread notification.",
        )

    def test_mark_read_requires_login(self):
        response = self.client.post(
            reverse(
                "notifications:mark_read",
                kwargs={"pk": self.notification.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_mark_read_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "notifications:mark_read",
                kwargs={"pk": self.notification.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.notification.refresh_from_db()

        self.assertFalse(
            self.notification.is_read,
        )

    def test_user_can_mark_own_notification_read(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "notifications:mark_read",
                kwargs={"pk": self.notification.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            reverse("notifications:list"),
        )

        self.notification.refresh_from_db()

        self.assertTrue(
            self.notification.is_read,
        )

    def test_user_cannot_mark_other_users_notification_read(self):
        other_notification = self.create_notification(
            recipient=self.other_user,
            message="Other notification.",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "notifications:mark_read",
                kwargs={"pk": other_notification.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        other_notification.refresh_from_db()

        self.assertFalse(
            other_notification.is_read,
        )

    def test_mark_read_shows_success_message(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "notifications:mark_read",
                kwargs={"pk": self.notification.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        messages = list(response.wsgi_request._messages)

        self.assertTrue(
            any(
                "Notification marked as read." in str(message)
                for message in messages
            )
        )

    def test_mark_read_nonexistent_notification_returns_404(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "notifications:mark_read",
                kwargs={"pk": 999999},
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class MarkAllNotificationsReadTests(
    NotificationTestMixin,
    TestCase,
):

    def setUp(self):
        self.user = self.create_user("user")
        self.other_user = self.create_user("other")

    def test_mark_all_read_requires_login(self):
        response = self.client.post(
            reverse("notifications:mark_all_read")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_mark_all_read_requires_post(self):
        self.create_notification(
            recipient=self.user,
            message="Unread notification.",
            is_read=False,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("notifications:mark_all_read")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                is_read=False,
            ).count(),
            1,
        )

    def test_user_can_mark_all_own_notifications_read(self):
        self.create_notification(
            recipient=self.user,
            message="Unread one.",
            is_read=False,
        )

        self.create_notification(
            recipient=self.user,
            message="Unread two.",
            is_read=False,
        )

        self.create_notification(
            recipient=self.user,
            message="Already read.",
            is_read=True,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("notifications:mark_all_read")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            reverse("notifications:list"),
        )

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                is_read=False,
            ).count(),
            0,
        )

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                is_read=True,
            ).count(),
            3,
        )

    def test_mark_all_read_does_not_change_other_users_notifications(self):
        self.create_notification(
            recipient=self.user,
            message="My unread.",
            is_read=False,
        )

        other_notification = self.create_notification(
            recipient=self.other_user,
            message="Other unread.",
            is_read=False,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("notifications:mark_all_read")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        other_notification.refresh_from_db()

        self.assertFalse(
            other_notification.is_read,
        )

    def test_mark_all_read_shows_success_message(self):
        self.create_notification(
            recipient=self.user,
            message="Unread notification.",
            is_read=False,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("notifications:mark_all_read"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        messages = list(response.wsgi_request._messages)

        self.assertTrue(
            any(
                "All notifications marked as read." in str(message)
                for message in messages
            )
        )