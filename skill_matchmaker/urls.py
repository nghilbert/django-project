from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic import TemplateView

from .forms.accounts import LoginForm
from .views.accounts import RegisterView
from .views.activation import ActivateView, ResendActivationView

urlpatterns = [
    path("accounts/register/", RegisterView.as_view(), name="register"),
    path("accounts/activate/resend/", ResendActivationView.as_view(), name="resend_activation"),
    path("accounts/activate/<uidb64>/<token>/", ActivateView.as_view(), name="activate"),
    path(
        "accounts/check-email/",
        TemplateView.as_view(template_name="skill_matchmaker/check_email.html"),
        name="check_email",
    ),
    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="skill_matchmaker/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
]
