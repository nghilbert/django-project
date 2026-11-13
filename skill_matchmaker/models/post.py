from django.conf import settings
from django.db import models
from django.urls import reverse


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

    def get_absolute_url(self):
        return reverse("post_detail", args=[self.pk])

    def reaction_summary(self, user):
        from .reaction import Reaction  # local import avoids circular import

        counts = dict(self.reactions.values_list("emoji").annotate(models.Count("id")))
        picked = self.reactions.filter(user=user).values_list("emoji", flat=True).first()
        return [
            {
                "value": value,
                "label": label,
                "count": counts.get(value, 0),
                "picked": value == picked,
            }
            for value, label in Reaction.Emoji.choices
        ]
