from django import forms


class ResendActivationForm(forms.Form):
    email = forms.EmailField()
