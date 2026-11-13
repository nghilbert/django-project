from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView

from ..forms.account_settings import AccountForm, EmailChangeForm
from ..models import User


class AccountSettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Lets the logged-in user edit their own account."""

    form_class = AccountForm
    template_name = "skill_matchmaker/account_settings.html"
    success_url = reverse_lazy("account_settings")
    success_message = "Your account was updated."

    def get_object(self, queryset=None):
        # Always edit the logged-in user, so users can only edit themselves
        return self.request.user


class EmailChangeView(LoginRequiredMixin, UpdateView):
    """Emails a confirmation link to the new address. The email doesn't change yet."""

    form_class = EmailChangeForm
    template_name = "skill_matchmaker/change_email.html"
    success_url = reverse_lazy("check_email")
    # The form sets the typed email on the object before checking it. Using a fresh copy
    # of the user, and not naming it "user" in the template, keeps a rejected email out of
    # the page (the nav bar shows "user").
    context_object_name = "account"

    def get_object(self, queryset=None):
        return User.objects.get(pk=self.request.user.pk)

    def form_valid(self, form):
        # Don't call super().form_valid(), which would save the email before it's confirmed
        if not self.object.send_email_change_link(self.request, form.instance.email):
            form.add_error(
                None,
                "We couldn't send the confirmation email. Your email address hasn't changed. "
                "Please try again in a few minutes.",
            )
            return self.form_invalid(form)
        return redirect(self.get_success_url())


class ConfirmEmailChangeView(View):
    def get(self, request, token):
        user = User.from_email_change_link(token)
        if user is None:
            return render(request, "skill_matchmaker/email_change_invalid.html")

        user.save(update_fields=["email"])
        return redirect("account_settings")
