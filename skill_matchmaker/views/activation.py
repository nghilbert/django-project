from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView

from ..account_links import ActivationLink
from ..forms.activation import ResendActivationForm
from ..models import User


class ActivateView(View):
    def get(self, request, uidb64, token):
        link = ActivationLink.from_url(uidb64, token)
        if link is None:
            return render(
                request,
                "skill_matchmaker/activation_invalid.html",
                {"form": ResendActivationForm(), "invalid_link": True},
            )

        link.confirm()
        return redirect("login")


class ResendActivationView(FormView):
    form_class = ResendActivationForm
    template_name = "skill_matchmaker/activation_invalid.html"
    success_url = reverse_lazy("check_email")

    def form_valid(self, form):
        email = form.cleaned_data["email"].lower()
        user = User.objects.filter(email=email, is_active=False).first()
        if user is not None:
            ActivationLink(user).send(self.request)
        # Delivery failures are logged, but the response stays identical for unknown,
        # active, and unverified addresses so it doesn't disclose account membership.
        return super().form_valid(form)
