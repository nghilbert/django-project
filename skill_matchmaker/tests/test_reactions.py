from django.test import TestCase
from django.urls import reverse

from skill_matchmaker.models import Post, Reaction, User


class ReactionToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password="test-password")
        self.post = Post.objects.create(author=self.user, title="Title", content="Content")

    def test_adds_switches_and_removes(self):
        Reaction.toggle(self.post, self.user, "heart")
        self.assertEqual(Reaction.objects.get().emoji, "heart")

        Reaction.toggle(self.post, self.user, "laugh")
        self.assertEqual(Reaction.objects.get().emoji, "laugh")

        Reaction.toggle(self.post, self.user, "laugh")
        self.assertFalse(Reaction.objects.exists())


class ReactViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password="test-password")
        self.post = Post.objects.create(author=self.user, title="Title", content="Content")
        self.url = reverse("react", args=[self.post.pk])
        self.client.force_login(self.user)

    def test_saves_reaction_and_redirects_to_next(self):
        response = self.client.post(self.url, {"emoji": "heart", "next": reverse("home")})
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(Reaction.objects.get().emoji, "heart")

    def test_falls_back_to_post_without_next(self):
        response = self.client.post(self.url, {"emoji": "heart"})
        self.assertRedirects(response, self.post.get_absolute_url())

    def test_ignores_next_on_another_site(self):
        response = self.client.post(self.url, {"emoji": "heart", "next": "https://example.com/"})
        self.assertRedirects(response, self.post.get_absolute_url())

    def test_rejects_unknown_emoji(self):
        response = self.client.post(self.url, {"emoji": "banana"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Reaction.objects.exists())

    def test_missing_post_is_404(self):
        response = self.client.post(reverse("react", args=[99999]), {"emoji": "heart"})
        self.assertEqual(response.status_code, 404)

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_logged_out_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(self.url, {"emoji": "heart"})
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        self.assertFalse(Reaction.objects.exists())
