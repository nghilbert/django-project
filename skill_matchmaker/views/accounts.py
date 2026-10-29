from django.urls import reverse_lazy
from django.views.generic import CreateView

from ..forms.accounts import RegistrationForm


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "skill_matchmaker/register.html"
    success_url = reverse_lazy("check_email")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.send_activation_email(self.request)
        return response
