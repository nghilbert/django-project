from abc import ABC, abstractmethod

from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.http import HttpRequest
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .email import send_account_email
from .models import User


class AccountLink(ABC):
    """A link emailed to a user that makes a change to their account when used."""

    email_subject: str
    email_message: str

    def __init__(self, user: User):
        self.user = user

    def send(self, request: HttpRequest) -> bool:
        url = request.build_absolute_uri(self._path())
        message = f"{self.email_message}\n\n{url}"
        return send_account_email(self.email_subject, message, self._recipient())

    @abstractmethod
    def _path(self) -> str: ...

    @abstractmethod
    def _recipient(self) -> str: ...

    @abstractmethod
    def confirm(self) -> None: ...


class ActivationLink(AccountLink):
    email_subject = "Verify your Skill Matchmaker account"
    email_message = "Click the link below to verify your account:"

    @classmethod
    def from_url(cls, uidb64: str, token: str) -> ActivationLink | None:
        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=user_id)
        except ValueError, TypeError, OverflowError, User.DoesNotExist:
            return None

        # Activating an account doesn't invalidate Django's password-reset token.
        if user.is_active or not default_token_generator.check_token(user, token):
            return None
        return cls(user)

    def _path(self) -> str:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        return reverse("activate", args=[uid, token])

    def _recipient(self) -> str:
        return self.user.email

    def confirm(self) -> None:
        self.user.activate()


class EmailChangeLink(AccountLink):
    email_subject = "Confirm your new Skill Matchmaker email"
    email_message = "Click the link below to confirm your new email:"
    salt = "change-email"
    # Expires after 3 days, like the sign-up link
    max_age = 60 * 60 * 24 * 3

    def __init__(self, user: User, new_email: str):
        super().__init__(user)
        self.new_email = new_email

    @classmethod
    def from_url(cls, token: str) -> EmailChangeLink | None:
        try:
            data = signing.loads(token, salt=cls.salt, max_age=cls.max_age)
        except signing.BadSignature:
            return None

        # Someone may have signed up with it since, or the link was already used
        if User.objects.filter(email=data["email"]).exists():
            return None

        user = User.objects.filter(pk=data["user"]).first()
        if user is None:
            return None
        return cls(user, data["email"])

    def _path(self) -> str:
        # Signing the new email in the token means it can't be edited without breaking the link
        token = signing.dumps({"user": self.user.pk, "email": self.new_email}, salt=self.salt)
        return reverse("confirm_email_change", args=[token])

    def _recipient(self) -> str:
        # The new address, not the user's current one, to prove the user owns it
        return self.new_email

    def confirm(self) -> None:
        self.user.change_email(self.new_email)
