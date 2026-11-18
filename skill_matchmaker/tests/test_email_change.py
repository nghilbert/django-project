"""Test created by Nathan Hilbert"""

import time
from unittest.mock import patch

from django.core import mail, signing
from django.test import TestCase
from django.urls import reverse

from skill_matchmaker.account_links import EmailChangeLink
from skill_matchmaker.models import User

ORIGINAL_EMAIL = "original@ilstu.edu"
NEW_EMAIL = "new@ilstu.edu"


class EmailChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=ORIGINAL_EMAIL)
        self.client.force_login(self.user)
        self.token = signing.dumps({"user": self.user.pk, "email": NEW_EMAIL}, salt="change-email")
        self.url = reverse("confirm_email_change", args=[self.token])

    def assertUserEmail(self, email):
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, email)

    def assertInvalidLinkPage(self, response):
        self.assertTemplateUsed(response, "skill_matchmaker/email_change_invalid.html")

    def test_request_sends_link_to_new_email(self):
        response = self.client.post(reverse("change_email"), {"email": NEW_EMAIL})

        self.assertRedirects(response, reverse("check_email"))
        self.assertEqual(mail.outbox[0].to, [NEW_EMAIL])
        self.assertUserEmail(ORIGINAL_EMAIL)

    def test_valid_link_changes_email(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("account_settings"))
        self.assertUserEmail(NEW_EMAIL)

    def test_expired_link_is_rejected(self):
        after_expiry = time.time() + EmailChangeLink.max_age + 1

        with patch("django.core.signing.time.time", return_value=after_expiry):
            response = self.client.get(self.url)

        self.assertInvalidLinkPage(response)
        self.assertUserEmail(ORIGINAL_EMAIL)

    def test_edited_link_is_rejected(self):
        response = self.client.get(reverse("confirm_email_change", args=[self.token + "x"]))

        self.assertInvalidLinkPage(response)
        self.assertUserEmail(ORIGINAL_EMAIL)

    def test_link_to_taken_email_is_rejected(self):
        User.objects.create_user(email=NEW_EMAIL)

        response = self.client.get(self.url)

        self.assertInvalidLinkPage(response)
        self.assertUserEmail(ORIGINAL_EMAIL)

    def test_link_for_deleted_user_is_rejected(self):
        self.user.delete()

        response = self.client.get(self.url)

        self.assertInvalidLinkPage(response)
