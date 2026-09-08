from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "John"
            }
        )
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Doe"
            }
        )
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "john@example.com"
            }
        )
    )

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "johndoe"
            }
        )
    )

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
            "password1",
            "password2",
        ]

    def clean_email(self):

        email = self.cleaned_data["email"].lower()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Create a password"
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm your password"
        })


class LoginForm(forms.Form):

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
                "autocomplete": "email",
            }
        )
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        )
    )


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "profile_image",
            "bio",
            "location",
            "skills",
        ]

        widgets = {

            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "username": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "profile_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Tell the community about yourself..."
                    ),
                }
            ),

            "skills": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Python, Django, JavaScript, UI/UX"
                    ),
                }
            ),

            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your city",
                }
            ),
        }


class EmailChangeForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "email",
        ]

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "setting-input",
                    "placeholder": "Enter your email address",
                    "autocomplete": "email",
                }
            ),
        }

        labels = {
            "email": "Email Address",
        }

    def clean_email(self):

        email = self.cleaned_data["email"].strip().lower()

        existing_user = User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).first()

        if existing_user:
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email