from django.conf import settings
from django.db import models

from .post import Post


class Comment(models.Model):
    """A comment a user writes on a post."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]  # Oldest first, so comments read like a conversation

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"
