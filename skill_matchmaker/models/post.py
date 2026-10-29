from django.conf import settings
from django.db import models


class Post(models.Model):
    """A post a user writes. Comments, events, and reactions build upon this class."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # posts come back sorted by newest first

    def __str__(self):
        return self.title
