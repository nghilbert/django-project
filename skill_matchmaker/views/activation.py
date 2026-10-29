from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView

from ..forms.activation import ResendActivationForm
from ..models import User


class ActivateView(View):
    def get(self, request, uidb64, token):
        user = User.from_activation_link(uidb64, token)
        if user is None:
            return render(
                request,
                "skill_matchmaker/activation_invalid.html",
                {"form": ResendActivationForm(), "invalid_link": True},
            )

        user.is_active = True
        user.save(update_fields=["is_active"])
        return redirect("login")


class ResendActivationView(FormView):
    form_class = ResendActivationForm
    template_name = "skill_matchmaker/activation_invalid.html"
    success_url = reverse_lazy("check_email")

    def form_valid(self, form):
        email = form.cleaned_data["email"].lower()
        user = User.objects.filter(email=email, is_active=False).first()
        if user is not None:
            user.send_activation_email(self.request)
        return super().form_valid(form)
