from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "inactive": "Your account is not verified yet. Check your email for a verification link.",
    }

    # Because User.USERNAME_FIELD is "email", the form's "username" field contains the email.
    def clean_username(self):
        return self.cleaned_data["username"].lower()
