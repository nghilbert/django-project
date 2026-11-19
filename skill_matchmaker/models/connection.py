from django.conf import settings
from django.db import models
from django.db.models.functions import Greatest, Least


class ConnectionQuerySet(models.QuerySet):
    """Connections looked up by who is in them and whether they've been accepted."""

    def between(self, a, b):
        return self.filter(models.Q(from_user=a, to_user=b) | models.Q(from_user=b, to_user=a))

    def involving(self, user):
        return self.filter(models.Q(from_user=user) | models.Q(to_user=user))

    def pending(self):
        return self.filter(status=Connection.Status.PENDING)

    def accepted(self):
        return self.filter(status=Connection.Status.ACCEPTED)


class Connection(models.Model):
    """A connection request from one user to another, which becomes a connection once accepted."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connections_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connections_received",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ConnectionQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Sorting the pair's ids makes A->B and B->A the same, so only one exists
            models.UniqueConstraint(
                Least("from_user", "to_user"),
                Greatest("from_user", "to_user"),
                name="one_connection_per_pair",
                violation_error_message="These users already have a connection or pending request.",
            ),
            models.CheckConstraint(
                condition=~models.Q(from_user=models.F("to_user")),
                name="no_self_connection",
                violation_error_message="User can't connect to themselves.",
            ),
        ]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.get_status_display()})"  # type: ignore

    def accept(self):
        """Turn a pending request into a connection."""
        self.status = self.Status.ACCEPTED
        self.save(update_fields=["status"])

    def deny(self):
        """Deny the request. It's deleted, so there's no denied status."""
        self.delete()

    def other_user(self, user):
        """Return the user in this connection who isn't the given user."""
        return self.to_user if user.pk == self.from_user_id else self.from_user  # type: ignore
