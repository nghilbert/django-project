from django.conf import settings
from django.db import models

from .post import Post


class Reaction(models.Model):
    """An emoji a user picked on a post."""

    class Emoji(models.TextChoices):
        HEART = "heart", "❤️"
        THUMBS_UP = "thumbs_up", "👍"
        THUMBS_DOWN = "thumbs_down", "👎"
        LAUGH = "laugh", "😂"

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    emoji = models.CharField(max_length=20, choices=Emoji.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # A user can react to a post once. To change emoji, update the existing reaction.
            models.UniqueConstraint(
                fields=["post", "user"],
                name="one_reaction_per_user_per_post",
            ),
        ]

    def __str__(self):
        return f"{self.get_emoji_display()} by {self.user} on {self.post}"  # type: ignore

    @classmethod
    def toggle(cls, post, user, emoji):
        """Add, switch, or remove the user's reaction on a post."""
        reaction = cls.objects.filter(post=post, user=user).first()
        if reaction is None:
            cls.objects.create(post=post, user=user, emoji=emoji)
        elif reaction.emoji == emoji:
            reaction.delete()
        else:
            reaction.emoji = emoji
            reaction.save(update_fields=["emoji"])
