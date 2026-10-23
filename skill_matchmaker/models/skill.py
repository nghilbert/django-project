from django.conf import settings
from django.db import models


class Skill(models.Model):
    """A skill from the list that admins maintain, like Guitar or Python."""

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """A skill a user can teach or wants to learn."""

    class SkillType(models.TextChoices):
        OFFERED = "offered", "Can teach"
        SOUGHT = "sought", "Want to learn"

    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="user_skills",
    )
    skill_type = models.CharField(max_length=10, choices=SkillType.choices)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)

    class Meta:
        constraints = [
            # The same skill can be added once to teach and once to learn, but not twice for either
            models.UniqueConstraint(
                fields=["user", "skill", "skill_type"],
                name="unique_user_skill_type",
            ),
        ]

    def __str__(self):
        return f"{self.user}: {self.skill} ({self.get_skill_type_display()})" # type: ignore