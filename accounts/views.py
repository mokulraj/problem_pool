from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from problems.models import Problem
from projects.models import Project
from solutions.models import Solution
from tasks.models import Task

from .forms import (
    LoginForm,
    ProfileForm,
    RegisterForm,
)
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
                backend="accounts.backends.EmailBackend",
            )

            messages.success(
                request,
                "Your account has been created successfully.",
            )

            return redirect("accounts:profile")

    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                email=email,
                password=password,
            )

            if user is not None:
                login(
                    request,
                    user,
                    backend="accounts.backends.EmailBackend",
                )

                messages.success(
                    request,
                    f"Welcome back, {user.first_name or user.username}!",
                )

                next_url = request.GET.get("next")

                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

                return redirect("/")

            messages.error(
                request,
                "Invalid email or password.",
            )

    else:
        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


@login_required
def logout_view(request):
    if request.method != "POST":
        return redirect("/")

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("/")


@login_required
def profile_view(request, username=None):
    if username:
        profile_user = get_object_or_404(
            User,
            username=username,
            is_active=True,
        )
    else:
        profile_user = request.user

    problems = (
        Problem.objects
        .filter(created_by=profile_user)
        .order_by("-created_at")
    )

    solutions = (
        Solution.objects
        .filter(proposed_by=profile_user)
        .select_related("problem")
        .order_by("-created_at")
    )

    projects = (
        Project.objects
        .filter(owner=profile_user)
        .order_by("-created_at")
    )

    completed_tasks_count = Task.objects.filter(
        assigned_to=profile_user,
        status=Task.Status.COMPLETED,
    ).count()

    context = {
        "profile_user": profile_user,
        "problems": problems,
        "solutions": solutions,
        "projects": projects,
        "problems_count": problems.count(),
        "solutions_count": solutions.count(),
        "projects_count": projects.count(),
        "completed_projects_count": projects.filter(
            status=Project.Status.COMPLETED,
        ).count(),
        "completed_tasks_count": completed_tasks_count,
    }

    return render(
        request,
        "accounts/profile.html",
        context,
    )


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect("accounts:profile")

    else:
        form = ProfileForm(
            instance=request.user,
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "form": form,
        },
    )