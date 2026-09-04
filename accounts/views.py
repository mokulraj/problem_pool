from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    LoginForm,
    ProfileForm,
    RegisterForm,
)


def register_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                "Your account has been created successfully."
            )

            login(
               request,
               user,
               backend="accounts.backends.EmailBackend"
           )

        return redirect("accounts:profile")

            

    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        form = LoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                email=email,
                password=password
            )

            if user is not None:

                login(
                    request,
                    user,
                    backend="accounts.backends.EmailBackend"
                )

                messages.success(
                    request,
                    f"Welcome back, {user.first_name or user.username}!"
                )

                next_url = request.GET.get("next")

                if next_url:
                    return redirect(next_url)

                return redirect("home")

            messages.error(
                request,
                "Invalid email or password."
            )

    else:
        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form
        }
    )


@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("home")


@login_required
def profile_view(request):

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": request.user
        }
    )

@login_required
def edit_profile_view(request):

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your profile has been updated successfully."
            )

            return redirect("accounts:profile")

    else:

        form = ProfileForm(
            instance=request.user
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "form": form
        }
    )