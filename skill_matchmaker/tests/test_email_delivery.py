import os
import runpy
from email import message_from_bytes, policy
from pathlib import Path
from smtplib import SMTPAuthenticationError, SMTPRecipientsRefused
from unittest.mock import patch
from urllib.parse import urlsplit

from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from skill_matchmaker.models import User

SMTP_MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "project@example.com",
            "password": "test-only-app-password",
            "use_tls": True,
            "timeout": 10,
        },
    },
}


class EmailConfigurationTests(SimpleTestCase):
    def load_settings(self, **environment):
        settings_path = Path(__file__).resolve().parents[2] / "config" / "settings.py"
        # Ignore the developer's real .env and never load their email credentials.
        with (
            patch.dict(os.environ, {"DJANGO_SECRET_KEY": "test-only", **environment}, clear=True),
            patch("dotenv.load_dotenv"),
        ):
            return runpy.run_path(str(settings_path))

    def test_console_is_default_without_credentials(self):
        config = self.load_settings()
        self.assertEqual(
            config["MAILERS"]["default"],
            {"BACKEND": "skill_matchmaker.email_backend.ConsoleEmailBackend"},
        )

    def test_gmail_settings_build_a_tls_mailer_without_connecting(self):
        config = self.load_settings(
            DJANGO_EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
            DJANGO_EMAIL_HOST_USER="project@example.com",
            DJANGO_EMAIL_HOST_PASSWORD="test-only-app-password",
        )
        with override_settings(MAILERS=config["MAILERS"]):
            backend = mail.mailers["default"]
            self.assertEqual(backend.host, "smtp.gmail.com")
            self.assertEqual(backend.port, 587)
            self.assertTrue(backend.use_tls)
            self.assertEqual(backend.timeout, 10)
            self.assertEqual(backend.username, "project@example.com")
            self.assertEqual(backend.password, "test-only-app-password")
            self.assertIsNone(backend.connection)
        self.assertEqual(config["DEFAULT_FROM_EMAIL"], "Skill Matchmaker <project@example.com>")

    def test_smtp_rejects_missing_credentials(self):
        for credentials in [
            {},
            {"DJANGO_EMAIL_HOST_USER": "project@example.com"},
            {"DJANGO_EMAIL_HOST_PASSWORD": "test-only-app-password"},
            {"DJANGO_EMAIL_HOST_USER": " ", "DJANGO_EMAIL_HOST_PASSWORD": " "},
        ]:
            with (
                self.subTest(credentials=list(credentials)),
                self.assertRaisesMessage(ImproperlyConfigured, "SMTP email requires"),
            ):
                self.load_settings(
                    DJANGO_EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
                    **credentials,
                )


@override_settings(
    MAILERS=SMTP_MAILERS,
    DEFAULT_FROM_EMAIL="Skill Matchmaker <project@example.com>",
)
class SmtpAccountEmailTests(TestCase):
    def setUp(self):
        # Exercise Django's SMTP backend and MIME serialization without network access.
        self.smtp_factory = self.enterContext(patch("django.core.mail.backends.smtp.smtplib.SMTP"))
        self.smtp = self.smtp_factory.return_value
        self.smtp.sendmail.return_value = {}
        self.data = {
            "email": "student@ilstu.edu",
            "first_name": "Test",
            "last_name": "Student",
            "password1": "CampusPractice847!",
            "password2": "CampusPractice847!",
        }

    def delivered_link(self, recipient):
        sender, recipients, raw_message = self.smtp.sendmail.call_args.args[:3]
        self.assertEqual(sender, "project@example.com")
        self.assertEqual(recipients, [recipient])
        message = message_from_bytes(raw_message, policy=policy.default)
        self.assertEqual(str(message["From"]), "Skill Matchmaker <project@example.com>")
        body = message.get_content()
        links = [line for line in body.splitlines() if line.startswith("http")]
        self.assertEqual(len(links), 1)
        self.assertEqual(urlsplit(links[0]).netloc, "testserver")
        return urlsplit(links[0]).path

    def test_signup_resend_and_email_change_deliver_working_links_over_smtp(self):
        response = self.client.post(reverse("register"), self.data)
        self.assertRedirects(response, reverse("check_email"))
        self.delivered_link("student@ilstu.edu")
        user = User.objects.get(email="student@ilstu.edu")
        self.assertFalse(user.is_active)

        response = self.client.post(reverse("resend_activation"), {"email": user.email})
        self.assertRedirects(response, reverse("check_email"))
        activation_link = self.delivered_link(user.email)
        self.assertRedirects(self.client.get(activation_link), reverse("login"))
        self.assertContains(self.client.get(activation_link), "invalid, expired, or already used")
        response = self.client.post(
            reverse("login"), {"username": user.email, "password": self.data["password1"]}
        )
        self.assertRedirects(response, reverse("home"))

        response = self.client.post(reverse("change_email"), {"email": "newstudent@ilstu.edu"})
        self.assertRedirects(response, reverse("check_email"))
        self.assertContains(self.client.get(reverse("check_email")), reverse("change_email"))
        change_link = self.delivered_link("newstudent@ilstu.edu")
        user.refresh_from_db()
        self.assertEqual(user.email, "student@ilstu.edu")
        self.assertRedirects(self.client.get(change_link), reverse("account_settings"))
        user.refresh_from_db()
        self.assertEqual(user.email, "newstudent@ilstu.edu")
        self.assertTemplateUsed(
            self.client.get(change_link), "skill_matchmaker/email_change_invalid.html"
        )

        self.assertEqual(self.smtp.sendmail.call_count, 3)
        self.assertEqual(self.smtp_factory.call_args.args, ("smtp.gmail.com", 587))
        self.assertEqual(self.smtp_factory.call_args.kwargs["timeout"], 10)
        self.assertEqual(self.smtp.starttls.call_count, 3)
        self.smtp.login.assert_called_with("project@example.com", "test-only-app-password")

    def test_signup_failure_preserves_inactive_account_and_resend_can_recover(self):
        self.smtp.login.side_effect = SMTPAuthenticationError(535, b"provider-private-details")
        with self.assertLogs("skill_matchmaker.email", level="WARNING") as logs:
            response = self.client.post(reverse("register"), self.data, follow=True)
        self.assertRedirects(response, reverse("resend_activation"))
        self.assertContains(response, "Your account was created")
        self.assertContains(response, "try again in a few minutes")
        self.assertNotContains(response, "provider-private-details")
        self.assertIn("SMTPAuthenticationError", " ".join(logs.output))
        self.assertNotIn("provider-private-details", " ".join(logs.output))
        user = User.objects.get(email="student@ilstu.edu")
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)

        self.smtp.login.side_effect = None
        response = self.client.post(reverse("resend_activation"), {"email": user.email})
        self.assertRedirects(response, reverse("check_email"))
        self.assertRedirects(self.client.get(self.delivered_link(user.email)), reverse("login"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(User.objects.count(), 1)

    def test_resend_failure_does_not_disclose_account_membership(self):
        user = User.objects.create_user(email="student@ilstu.edu", is_active=False)
        self.smtp.sendmail.side_effect = TimeoutError("private transport details")
        with self.assertLogs("skill_matchmaker.email", level="WARNING"):
            failed = self.client.post(
                reverse("resend_activation"), {"email": user.email}, follow=True
            )
        self.assertRedirects(failed, reverse("check_email"))
        self.assertContains(failed, "If no email arrives, try again")
        self.assertNotContains(failed, "we sent you a link")
        user.is_active = True
        user.save()
        for address in [user.email, "unknown@ilstu.edu"]:
            response = self.client.post(
                reverse("resend_activation"), {"email": address}, follow=True
            )
            self.assertEqual(response.content, failed.content)
        self.assertEqual(self.smtp.sendmail.call_count, 1)

    def test_email_change_failure_keeps_original_address_and_allows_retry(self):
        user = User.objects.create_user(email="student@ilstu.edu")
        self.client.force_login(user)
        self.smtp.sendmail.side_effect = SMTPRecipientsRefused(
            {"newstudent@ilstu.edu": (550, b"private provider details")}
        )
        with self.assertLogs("skill_matchmaker.email", level="WARNING"):
            response = self.client.post(reverse("change_email"), {"email": "newstudent@ilstu.edu"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("__all__", response.context["form"].errors)
        self.assertContains(response, "Your email address hasn")
        self.assertNotContains(response, "private provider details")
        user.refresh_from_db()
        self.assertEqual(user.email, "student@ilstu.edu")

        self.smtp.sendmail.side_effect = None
        response = self.client.post(reverse("change_email"), {"email": "newstudent@ilstu.edu"})
        self.assertRedirects(response, reverse("check_email"))
        self.assertRedirects(
            self.client.get(self.delivered_link("newstudent@ilstu.edu")),
            reverse("account_settings"),
        )
        user.refresh_from_db()
        self.assertEqual(user.email, "newstudent@ilstu.edu")

    def test_backend_accepting_zero_messages_offers_signup_recovery(self):
        with (
            patch("skill_matchmaker.email.send_mail", return_value=0),
            self.assertLogs("skill_matchmaker.email", level="WARNING"),
        ):
            response = self.client.post(reverse("register"), self.data)
        self.assertRedirects(response, reverse("resend_activation"))
        self.assertFalse(User.objects.get(email="student@ilstu.edu").is_active)
