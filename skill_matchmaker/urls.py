from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.urls import path
from django.views.generic import TemplateView

from .forms.accounts import LoginForm
from .views import AccountSettingsView, RemoveSkillView, SkillsView
from .views.accounts import RegisterView
from .views.activation import ActivateView, ResendActivationView
from .views.home import HomeView
from .views.posts import PostCreateView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("posts/new/", PostCreateView.as_view(), name="create_post"),
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
    path(
        "accounts/skills/",
        SkillsView.as_view(),
        name="skills",
    ),
    path(
        "accounts/skills/<int:pk>/remove/",
        RemoveSkillView.as_view(),
        name="remove_skill",
    ),
]
