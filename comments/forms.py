from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment

        fields = [
            "content",
        ]

        widgets = {

            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Share your thoughts, feedback, "
                        "or ideas..."
                    ),
                }
            ),

        }

    def clean_content(self):

        content = self.cleaned_data["content"].strip()

        if len(content) < 3:
            raise forms.ValidationError(
                "Comment must contain at least 3 characters."
            )

        if len(content) > 2000:
            raise forms.ValidationError(
                "Comment cannot exceed 2000 characters."
            )

        return content