from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task

        fields = [
            "title",
            "description",
            "assigned_to",
            "due_date",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter task title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Describe this task...",
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.project = project

        if project is not None:
            member_ids = project.team_memberships.values_list(
                "user_id",
                flat=True,
            )

            self.fields["assigned_to"].queryset = (
                self.fields["assigned_to"]
                .queryset
                .filter(
                    id__in=list(member_ids)
                )
            )

    def clean(self):
        cleaned_data = super().clean()

        due_date = cleaned_data.get("due_date")

        if (
            due_date
            and self.project
            and self.project.end_date
            and due_date > self.project.end_date
        ):
            self.add_error(
                "due_date",
                "Task due date cannot be after the project deadline.",
            )

        return cleaned_data