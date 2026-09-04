from django import forms

from .models import Solution


class SolutionForm(forms.ModelForm):

    class Meta:
        model = Solution

        fields = [
            "title",
            "description",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Digital token system for canteen"
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": (
                        "Explain your proposed solution, "
                        "how it works, and why it could solve "
                        "the problem..."
                    ),
                }
            ),
        }

    def clean_title(self):

        title = self.cleaned_data["title"].strip()

        if len(title) < 10:
            raise forms.ValidationError(
                "Solution title must contain at least 10 characters."
            )

        return title

    def clean_description(self):

        description = self.cleaned_data["description"].strip()

        if len(description) < 30:
            raise forms.ValidationError(
                "Please provide at least 30 characters describing your solution."
            )

        return description