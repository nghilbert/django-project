from django.contrib.auth.views import LoginView
from django.urls import path

from .forms.accounts import LoginForm

urlpatterns = [
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
