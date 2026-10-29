from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.urls import path

from .forms.accounts import LoginForm
from .views import AccountSettingsView
from .views.home import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="skill_matchmaker/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path(
        "accounts/settings/",
        AccountSettingsView.as_view(),
        name="account_settings",
    ),
    path(
        "accounts/password/",
        PasswordChangeView.as_view(template_name="skill_matchmaker/password_change.html"),
        name="password_change",
    ),
    path(
        "accounts/password/done/",
        PasswordChangeDoneView.as_view(template_name="skill_matchmaker/password_change_done.html"),
        name="password_change_done",
    ),
]
