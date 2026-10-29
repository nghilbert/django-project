from django import forms

from ..models import UserSkill


class UserSkillForm(forms.ModelForm):
    """Lets a user add a skill they can teach or want to learn."""

    class Meta:
        model = UserSkill
        fields = ["skill", "skill_type", "level"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        # Needed to check for duplicates, since user isn't a field on the form
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        skill = cleaned_data.get("skill")
        skill_type = cleaned_data.get("skill_type")

        if UserSkill.objects.filter(user=self.user, skill=skill, skill_type=skill_type).exists():
            self.add_error("skill", "You already added this skill.")

        return cleaned_data
