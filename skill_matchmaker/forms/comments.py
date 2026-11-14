from django.forms import ModelForm

from ..models import Comment


class CommentForm(ModelForm):
    """Lets a user write a comment on a post."""

    class Meta:
        model = Comment
        fields = ["content"]
        # The form strips spaces, so a comment of only spaces is blank too
        error_messages = {"content": {"required": "Enter a comment"}}
