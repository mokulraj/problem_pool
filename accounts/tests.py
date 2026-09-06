from io import BytesIO

from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import User
from problems.models import Problem
from solutions.models import Solution
from projects.models import Project
from tasks.models import Task


class AccountTestMixin:

    def create_user(
        self,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        **extra_fields,
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Test",
            last_name="User",
            **extra_fields,
        )

    def create_problem(self, user):
        return Problem.objects.create(
            title="A valid test problem",
            description=(
                "This is a valid test problem description "
                "with enough characters."
            ),
            category=Problem.Category.CAMPUS,
            location="Test Campus",
            created_by=user,
        )


class RegistrationTests(AccountTestMixin, TestCase):

    def test_register_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "username": "johndoe",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

        user = User.objects.get(
            username="johndoe"
        )

        self.assertEqual(
            user.email,
            "john@example.com",
        )

        self.assertTrue(
            self.client.session.get("_auth_user_id")
        )


class LoginTests(AccountTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

    def test_valid_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email,
                "password": "TestPassword123!",
            },
        )

        self.assertRedirects(
            response,
            "/",
        )

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.user.pk,
        )

    def test_invalid_password_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email,
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            self.client.session.get("_auth_user_id")
        )

    def test_login_with_case_insensitive_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email.upper(),
                "password": "TestPassword123!",
            },
        )

        self.assertRedirects(
            response,
            "/",
        )

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.user.pk,
        )

    def test_external_next_url_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login")
            + "?next=https://evil.example.com",
            {
                "email": self.user.email,
                "password": "TestPassword123!",
            },
        )

        self.assertRedirects(
            response,
            "/",
        )


class LogoutTests(AccountTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()
        self.client.force_login(self.user)

    def test_logout_requires_post(self):
        response = self.client.get(
            reverse("accounts:logout")
        )

        self.assertRedirects(
            response,
            "/",
        )

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.user.pk,
        )

    def test_logout_with_post(self):
        response = self.client.post(
            reverse("accounts:logout")
        )

        self.assertRedirects(
            response,
            "/",
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )


class ProfileAccessTests(AccountTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

        self.other_user = self.create_user(
            username="otheruser",
            email="other@example.com",
        )

    def test_anonymous_user_cannot_access_profile(self):
        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertRedirects(
            response,
            f"/login/?next={reverse('accounts:profile')}",
        )

    def test_authenticated_user_can_access_own_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["profile_user"],
            self.user,
        )

    def test_authenticated_user_can_access_active_public_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "accounts:public_profile",
                kwargs={
                    "username": self.other_user.username,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["profile_user"],
            self.other_user,
        )

    def test_inactive_user_public_profile_returns_404(self):
        self.other_user.is_active = False

        self.other_user.save(
            update_fields=["is_active"]
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "accounts:public_profile",
                kwargs={
                    "username": self.other_user.username,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class ProfileDataTests(AccountTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user()

        self.client.force_login(self.user)

    def test_profile_counts_are_calculated(self):
        problem = self.create_problem(self.user)

        Solution.objects.create(
            problem=problem,
            proposed_by=self.user,
            title="A valid solution",
            description=(
                "This is a valid solution description "
                "with enough characters."
            ),
        )

        project = Project.objects.create(
            problem=problem,
            selected_solution=problem.solutions.first(),
            name="Test Project",
            description="A valid test project description.",
            owner=self.user,
        )

        Task.objects.create(
            project=project,
            title="Completed task",
            assigned_to=self.user,
            status=Task.Status.COMPLETED,
        )

        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["problems_count"],
            1,
        )

        self.assertEqual(
            response.context["solutions_count"],
            1,
        )

        self.assertEqual(
            response.context["projects_count"],
            1,
        )

        self.assertEqual(
            response.context["completed_projects_count"],
            0,
        )

        self.assertEqual(
            response.context["completed_tasks_count"],
            1,
        )

    def test_profile_form_cannot_change_role_or_points(self):
        original_role = self.user.role
        original_points = self.user.points

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Changed",
                "last_name": "User",
                "username": self.user.username,
                "bio": "Updated biography.",
                "location": "Updated City",
                "skills": "Django, Python",
                "role": User.Role.ADMIN,
                "points": 999999,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.role,
            original_role,
        )

        self.assertEqual(
            self.user.points,
            original_points,
        )

        self.assertEqual(
            self.user.first_name,
            "Changed",
        )

    def test_edit_profile_requires_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("accounts:edit_profile")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_edit_profile_get_displays_form(self):
        response = self.client.get(
            reverse("accounts:edit_profile")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "accounts/edit_profile.html",
        )

        self.assertIn(
            "form",
            response.context,
        )

    def test_edit_profile_updates_allowed_fields(self):
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Updated",
                "last_name": "Person",
                "username": self.user.username,
                "bio": "I build useful solutions.",
                "location": "New City",
                "skills": "Python, Django, SQL",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Updated",
        )

        self.assertEqual(
            self.user.last_name,
            "Person",
        )

        self.assertEqual(
            self.user.bio,
            "I build useful solutions.",
        )

        self.assertEqual(
            self.user.location,
            "New City",
        )

        self.assertEqual(
            self.user.skills,
            "Python, Django, SQL",
        )

    def test_edit_profile_can_upload_profile_image(self):
        image_file = BytesIO()

        image = Image.new(
            "RGB",
            (100, 100),
            "white",
        )

        image.save(
            image_file,
            format="PNG",
        )

        uploaded_image = SimpleUploadedFile(
            "profile.png",
            image_file.getvalue(),
            content_type="image/png",
        )

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Image",
                "last_name": "User",
                "username": self.user.username,
                "bio": "Profile image test.",
                "location": "Test City",
                "skills": "Testing",
                "profile_image": uploaded_image,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

        self.user.refresh_from_db()

        self.assertTrue(
            bool(self.user.profile_image)
        )

    def test_profile_form_does_not_expose_role_or_points(self):
        from .forms import ProfileForm

        form = ProfileForm(
            instance=self.user
        )

        self.assertNotIn(
            "role",
            form.fields,
        )

        self.assertNotIn(
            "points",
            form.fields,
        )

    def test_profile_form_contains_expected_fields(self):
        from .forms import ProfileForm

        form = ProfileForm(
            instance=self.user
        )

        expected_fields = {
            "first_name",
            "last_name",
            "username",
            "profile_image",
            "bio",
            "location",
            "skills",
        }

        self.assertEqual(
            set(form.fields.keys()),
            expected_fields,
        )

    def test_profile_update_does_not_change_points(self):
        self.user.points = 125

        self.user.save(
            update_fields=["points"]
        )

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Points",
                "last_name": "Protected",
                "username": self.user.username,
                "bio": "Points must remain unchanged.",
                "location": "Test City",
                "skills": "Python",
                "points": 999999,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            125,
        )

    def test_profile_update_does_not_change_role(self):
        original_role = self.user.role

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Role",
                "last_name": "Protected",
                "username": self.user.username,
                "bio": "Role must remain unchanged.",
                "location": "Test City",
                "skills": "Django",
                "role": User.Role.ADMIN,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.role,
            original_role,
        )