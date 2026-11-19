from django.db import models

from .post import Post
from .skill import Skill


class CampusLocation(models.Model):
    """A campus room from the list that admins maintain, like Milner Library 201."""

    building = models.CharField(max_length=100)
    room = models.CharField(max_length=50)

    class Meta:
        ordering = ["building", "room"]
        constraints = [
            models.UniqueConstraint(
                fields=["building", "room"],
                name="unique_campus_location",
                violation_error_message="This building and room already exist.",
            ),
        ]

    def __str__(self):
        return f"{self.building} {self.room}"


class Event(Post):
    """A post with a start time and skill, held at a campus location, a meeting link, or both."""

    starts_at = models.DateTimeField()
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,  # can't delete a skill that events use
        related_name="events",
    )
    location = models.ForeignKey(
        CampusLocation,
        on_delete=models.PROTECT,  # can't delete a location that events use
        null=True,
        blank=True,
        related_name="events",
    )
    meeting_link = models.URLField(blank=True)

    class Meta:
        # Post's ordering (-created_at) is inherited because this Meta doesn't set one
        constraints = [
            models.CheckConstraint(
                condition=models.Q(location__isnull=False) | ~models.Q(meeting_link=""),
                name="event_has_location_or_link",
                violation_error_message="Add a location or a meeting link.",
            ),
        ]
