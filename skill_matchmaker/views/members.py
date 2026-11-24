from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from ..models import Connection, User


class MemberProfileView(LoginRequiredMixin, DetailView):
    """Shows a member's profile while keeping the viewer as the template's user."""

    model = User
    context_object_name = "member"
    template_name = "skill_matchmaker/member_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # None when there is no request or connection between the viewer and this member
        context["connection"] = Connection.objects.between(self.request.user, self.object).first()
        return context
