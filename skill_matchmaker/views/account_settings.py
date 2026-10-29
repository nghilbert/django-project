from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from ..forms.account_settings import AccountForm


class AccountSettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Lets the logged-in user edit their own account."""

    form_class = AccountForm
    template_name = "skill_matchmaker/account_settings.html"
    success_url = reverse_lazy("account_settings")
    success_message = "Your account was updated."

    def get_object(self, queryset=None):
        # Always edit the logged-in user, so users can only edit themselves
        return self.request.user
