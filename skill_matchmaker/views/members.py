from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from ..models import User


class MemberProfileView(LoginRequiredMixin, DetailView):
    """Shows a member's profile while keeping the viewer as the template's user."""

    model = User
    context_object_name = "member"
    template_name = "skill_matchmaker/member_profile.html"
