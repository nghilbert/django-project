from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm

from ..models import User


class IlstuEmailField(forms.EmailField):
    def validate(self, value):
        super().validate(value)
        if not value.lower().endswith("@ilstu.edu"):
            raise forms.ValidationError("Use your @ilstu.edu email.")


class RegistrationForm(BaseUserCreationForm):
    email = IlstuEmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "inactive": "Your account is not verified yet. Check your email for a verification link.",
    }

    # Because User.USERNAME_FIELD is "email", the form's "username" field contains the email.
    def clean_username(self):
        return self.cleaned_data["username"].lower()


class DeleteAccountForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password
