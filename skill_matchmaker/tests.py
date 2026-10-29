from django.test import TestCase
from django.urls import reverse

from skill_matchmaker.models import User


class NavigationTests(TestCase):
    def test_logged_out_navigation_is_shown_on_login_page(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertContains(response, "Sign up")
        self.assertContains(response, 'href="/accounts/register/"')

    def test_logged_in_navigation_and_logout(self):
        user = User.objects.create_user(email="person@example.com", password="test-password")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, f'href="{reverse("home")}"')
        self.assertContains(response, "Logged in as")
        self.assertContains(response, "person@example.com")
        self.assertContains(response, f'action="{reverse("logout")}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_rejects_get_requests(self):
        user = User.objects.create_user(email="person@example.com", password="test-password")
        self.client.force_login(user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
