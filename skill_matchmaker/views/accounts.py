from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView

from ..forms.accounts import DeleteAccountForm, RegistrationForm


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "skill_matchmaker/register.html"
    success_url = reverse_lazy("check_email")

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.object.send_activation_email(self.request):
            messages.error(
                self.request,
                "Your account was created, but we couldn't send the verification email. "
                "Use the form below to try again in a few minutes.",
            )
            return redirect("resend_activation")
        return response


class DeleteAccountView(LoginRequiredMixin, DeleteView):
    form_class = DeleteAccountForm
    template_name = "skill_matchmaker/account_confirm_delete.html"
    success_url = reverse_lazy("account_deleted")

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        logout(self.request)
        return super().form_valid(form)
