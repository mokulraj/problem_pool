from django.contrib.auth import views as auth_views
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponseRedirect
from django.urls import path, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import FormView

from . import views


app_name = "accounts"


@method_decorator(
    [
        sensitive_post_parameters(),
        csrf_protect,
        never_cache,
    ],
    name="dispatch",
)
class ProblemPoolPasswordResetConfirmView(
    auth_views.PasswordResetConfirmView
):
    """
    ProblemPool password-reset confirmation view.

    Unlike Django's default PasswordResetConfirmView, this view keeps
    validating the original reset token from the URL instead of storing
    the token in the session and redirecting to a second URL.

    This avoids losing the temporary password-reset session during
    real-browser navigation while preserving Django's secure token
    validation and SetPasswordForm validation.
    """

    def dispatch(self, request, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]

            if self.token_generator.check_token(self.user, token):
                self.validlink = True

                # Call FormView.dispatch directly so Django's default
                # PasswordResetConfirmView doesn't redirect to the
                # session-dependent /set-password/ URL.
                return FormView.dispatch(
                    self,
                    request,
                    *args,
                    **kwargs,
                )

        return self.render_to_response(
            self.get_context_data()
        )

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            pk = self.get_user_model()._meta.pk.to_python(uid)
            user = self.get_user_model()._default_manager.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            self.get_user_model().DoesNotExist,
            ValidationError,
        ):
            user = None

        return user

    def get_user_model(self):
        from django.contrib.auth import get_user_model

        return get_user_model()

    def form_valid(self, form):
        """
        Save the new password and redirect to the completion page.

        No temporary reset token is removed from the session because
        this ProblemPool flow does not depend on that session token.
        """
        form.save()

        return HttpResponseRedirect(
            self.get_success_url()
        )


urlpatterns = [

    # ============================================================
    # AUTHENTICATION
    # ============================================================

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "register/",
        views.register_view,
        name="register",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),


    # ============================================================
    # PASSWORD RESET
    # ============================================================

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy(
                "accounts:password_reset_done"
            ),
        ),
        name="password_reset",
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        ProblemPoolPasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy(
                "accounts:password_reset_complete"
            ),
        ),
        name="password_reset_confirm",
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),


    # ============================================================
    # PROFILE
    # ============================================================

    path(
        "profile/",
        views.profile_view,
        name="profile",
    ),

    path(
        "profile/edit/",
        views.edit_profile_view,
        name="edit_profile",
    ),


    # ============================================================
    # ACCOUNT SETTINGS
    # Dedicated separate page
    # ============================================================

    path(
        "account-settings/",
        views.account_settings_view,
        name="account_settings",
    ),


    # ============================================================
    # PUBLIC PROFILE
    # ============================================================

    path(
        "profile/<str:username>/",
        views.profile_view,
        name="public_profile",
    ),
]