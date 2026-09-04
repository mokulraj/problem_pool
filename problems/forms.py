from django import forms

from .models import Problem


class ProblemForm(forms.ModelForm):

    class Meta:
        model = Problem

        fields = [
            "title",
            "description",
            "category",
            "location",
            "priority",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Long queues in college canteen"
                    ),
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "placeholder": (
                        "Describe the problem clearly..."
                    ),
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: College Campus",
                }
            ),

            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if len(title) < 10:
            raise forms.ValidationError(
                "Problem title must contain at least 10 characters."
            )

        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()

        if len(description) < 30:
            raise forms.ValidationError(
                "Please provide at least 30 characters describing the problem."
            )

        return description