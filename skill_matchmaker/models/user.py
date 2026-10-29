from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class UserManager(BaseUserManager):
    """Creates users with an email instead of a username."""

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        # Lowercase the whole email, normalize_email only lowercases the domain
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """A user who logs in with their email."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)  # Can log into /admin/
    is_active = models.BooleanField(default=True)  # Can log in
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"

    # Keep Meta options from both parent classes
    class Meta(AbstractBaseUser.Meta, PermissionsMixin.Meta):
        pass

    def clean(self):
        # Lowercase emails saved through forms
        super().clean()
        self.email = self.email.lower()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def email_user(self, subject: str, message: str, from_email: str | None = None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def send_activation_email(self, request):
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        link = request.build_absolute_uri(reverse("activate", args=[uid, token]))
        self.email_user(
            "Verify your Skill Matchmaker account",
            f"Click this link to verify your account:\n\n{link}",
        )

    @classmethod
    def from_activation_link(cls, uidb64, token):
        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = cls.objects.get(pk=user_id)
        except ValueError, TypeError, OverflowError, cls.DoesNotExist:
            return None

        # Activating an account doesn't invalidate Django's password-reset token.
        if user.is_active or not default_token_generator.check_token(user, token):
            return None
        return user
