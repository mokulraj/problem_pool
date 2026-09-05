from django import forms

from .models import JoinRequest


class JoinRequestForm(forms.ModelForm):
    class Meta:
        model = JoinRequest

        fields = [
            "message",
        ]

        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Tell the project owner why you would "
                        "like to join this project..."
                    ),
                }
            ),
        }