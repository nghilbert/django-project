from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..email import send_account_email


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
        extra_fields.setdefault("is_superuser", True)
        return Admin.objects.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """A user who logs in with their email."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True)
    is_active = models.BooleanField(default=True)  # Can log in
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"

    # Keep Meta options from both parent classes
    class Meta(AbstractBaseUser.Meta, PermissionsMixin.Meta):
        pass

    @property
    def is_staff(self) -> bool:
        # Django's /admin/ lets in only users whose is_staff is True
        return hasattr(self, "admin")

    def clean(self):
        # Lowercase emails saved through forms
        super().clean()
        self.email = self.email.lower()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_absolute_url(self):
        return reverse("member_profile", args=[self.pk])

    def activate(self):
        self.is_active = True
        self.save(update_fields=["is_active"])

    def change_email(self, email: str):
        self.email = email
        self.save(update_fields=["email"])

    def email_user(self, subject: str, message: str, from_email: str | None = None, **kwargs):
        return send_account_email(subject, message, self.email, from_email, **kwargs)

    def delete(self, using=None, keep_parents=False):
        # keep_parents=True deletes only a subclass row, so the user keeps their picture
        if not keep_parents:
            self.profile_picture.delete(save=False)
        return super().delete(using=using, keep_parents=keep_parents)


class Admin(User):
    """A user who manages the site and can use /admin/."""

    @classmethod
    def promote(cls, user: User) -> Admin:
        # Saving a subclass also saves its User row.
        # Build it from the stored values to leave the user unchanged
        row = User.objects.values().get(pk=user.pk)
        admin = cls(user_ptr=user, **row)
        admin.save()
        return admin

    def demote(self):
        self.delete(keep_parents=True)
