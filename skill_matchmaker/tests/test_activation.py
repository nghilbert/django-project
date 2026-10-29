from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from skill_matchmaker.forms.accounts import LoginForm
from skill_matchmaker.models import User


class ActivationTests(TestCase):
    def setUp(self):
        self.password = "CampusPractice847!"
        self.user = User.objects.create_user(
            email="student@ilstu.edu", password=self.password, is_active=False
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.url = reverse("activate", args=[self.uid, self.token])

    def test_send_activation_email(self):
        request = RequestFactory().get("/accounts/register/", secure=True)
        self.user.send_activation_email(request)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        link = urlsplit(mail.outbox[0].body.splitlines()[-1])
        self.assertEqual(link.scheme, "https")
        self.assertEqual(link.netloc, "testserver")
        match = resolve(link.path)
        self.assertEqual(
            User.from_activation_link(match.kwargs["uidb64"], match.kwargs["token"]), self.user
        )

    def test_registration_emails_working_activation_link(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "NewStudent@ILSTU.EDU",
                "first_name": "New",
                "last_name": "Student",
                "password1": self.password,
                "password2": self.password,
            },
        )
        self.assertRedirects(response, reverse("check_email"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["newstudent@ilstu.edu"])
        user = User.objects.get(email="newstudent@ilstu.edu")
        self.assertFalse(user.is_active)
        link = mail.outbox[0].body.splitlines()[-1]
        self.assertRedirects(self.client.get(urlsplit(link).path), reverse("login"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        form = LoginForm(data={"username": user.email, "password": self.password})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_link_activates_without_logging_in(self):
        self.assertEqual(User.from_activation_link(self.uid, self.token), self.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_used_link_is_rejected_before_first_login(self):
        self.client.get(self.url)
        self.assertIsNone(User.from_activation_link(self.uid, self.token))
        response = self.client.get(self.url)
        self.assertContains(response, "invalid, expired, or already used")
        self.assertContains(response, reverse("resend_activation"))

    def test_invalid_user_ids_do_not_crash(self):
        for value in [b"not-a-number", b"999999", b"9" * 100, b"\xff"]:
            with self.subTest(value=value):
                uid = urlsafe_base64_encode(value)
                self.assertIsNone(User.from_activation_link(uid, self.token))
                response = self.client.get(reverse("activate", args=[uid, self.token]))
                self.assertContains(response, "invalid, expired, or already used")
        self.assertIsNone(User.from_activation_link("!", self.token))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_invalid_tokens_do_not_activate(self):
        for token in ["made-up", self.token + "x"]:
            with self.subTest(token=token):
                response = self.client.get(reverse("activate", args=[self.uid, token]))
                self.assertContains(response, "invalid, expired, or already used")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_token_cannot_activate_another_user(self):
        other = User.objects.create_user(email="other@ilstu.edu", is_active=False)
        uid = urlsafe_base64_encode(force_bytes(other.pk))
        self.assertIsNone(User.from_activation_link(uid, self.token))

    def test_expired_link_is_rejected(self):
        later = datetime.now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 1)
        with patch.object(default_token_generator, "_now", return_value=later):
            response = self.client.get(self.url)
        self.assertContains(response, "invalid, expired, or already used")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_resend_accepts_mixed_case_and_sends_working_link(self):
        response = self.client.post(reverse("resend_activation"), {"email": "STUDENT@ILSTU.EDU"})
        self.assertRedirects(response, reverse("check_email"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        link = mail.outbox[0].body.splitlines()[-1]
        self.assertRedirects(self.client.get(urlsplit(link).path), reverse("login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_resend_does_not_reveal_unknown_or_active_accounts(self):
        response = self.client.post(
            reverse("resend_activation"), {"email": self.user.email}, follow=True
        )
        confirmation = response.content
        self.user.is_active = True
        self.user.save()
        mail.outbox.clear()
        for email in [self.user.email, "unknown@ilstu.edu", "unknown@example.com"]:
            with self.subTest(email=email):
                response = self.client.post(
                    reverse("resend_activation"), {"email": email}, follow=True
                )
                self.assertRedirects(response, reverse("check_email"))
                self.assertEqual(response.content, confirmation)
                self.assertEqual(len(mail.outbox), 0)
                self.assertEqual(User.objects.count(), 1)

    def test_resend_rejects_missing_or_malformed_email(self):
        for email in ["", "not-an-email"]:
            with self.subTest(email=email):
                response = self.client.post(reverse("resend_activation"), {"email": email})
                self.assertEqual(response.status_code, 200)
                self.assertIn("email", response.context["form"].errors)
                self.assertEqual(len(mail.outbox), 0)

    def test_resend_page_is_available(self):
        response = self.client.get(reverse("resend_activation"))
        self.assertContains(response, "Resend verification email")
        self.assertNotContains(response, "invalid, expired, or already used")
