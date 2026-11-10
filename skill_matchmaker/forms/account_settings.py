from django import forms
from django.core.files.uploadedfile import UploadedFile

from ..models import User
from .accounts import IlstuEmailField

MAX_PICTURE_SIZE = 2 * 1024 * 1024  # 2 MB


class AccountForm(forms.ModelForm):
    """Lets a user edit their name, bio, and profile picture."""

    # Declared to make them required, since blank names not allowed
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "bio", "profile_picture"]

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")

        # Only check new uploads. A picture that's already saved passed this check before.
        if isinstance(picture, UploadedFile) and picture.size > MAX_PICTURE_SIZE:
            raise forms.ValidationError("Pictures must be 2 MB or smaller.")

        return picture


class EmailChangeForm(forms.ModelForm):
    """Asks for a new @ilstu.edu email. The model lowercases it and rejects one that's taken."""

    email = IlstuEmailField()

    class Meta:
        model = User
        fields = ["email"]
