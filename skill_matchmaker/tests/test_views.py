from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from skill_matchmaker.models import Post, User


class NavigationTests(TestCase):
    def test_logged_out_navigation_is_shown_on_login_page(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertNotContains(response, f'href="{reverse("create_post")}"')
        self.assertContains(response, "Sign up")
        self.assertContains(response, 'href="/accounts/register/"')

    def test_logged_in_navigation_and_logout(self):
        user = User.objects.create_user(email="person@example.com", password="test-password")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, f'href="{reverse("home")}"')
        self.assertContains(response, f'href="{reverse("create_post")}">+ New post</a>')
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


class HomeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password="test-password")
        self.client.force_login(self.user)

    def test_home_displays_posts_newest_first_with_post_details(self):
        older_post = Post.objects.create(
            author=self.user,
            title="Older post",
            content="First line\nSecond line",
        )
        newer_post = Post.objects.create(
            author=self.user,
            title="Newer post",
            content="Newest content",
        )
        now = timezone.now()
        Post.objects.filter(pk=older_post.pk).update(created_at=now - timedelta(days=1))
        Post.objects.filter(pk=newer_post.pk).update(created_at=now)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [post.title for post in response.context["posts"]],
            ["Newer post", "Older post"],
        )
        self.assertContains(response, "person@example.com")
        self.assertContains(response, date_format(now, "F j, Y"))
        self.assertContains(response, "Newest content")
        self.assertContains(response, "First line<br>Second line")

    def test_home_shows_empty_state_when_there_are_no_posts(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "No posts yet.")

    def test_long_home_post_is_truncated_with_read_more_link(self):
        words = [f"word{number}" for number in range(1, 61)]
        post = Post.objects.create(
            author=self.user,
            title="A long post",
            content=" ".join(words),
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, "word50 \u2026")
        self.assertNotContains(response, "word51")
        self.assertNotContains(response, "word60")
        self.assertContains(
            response,
            f'<a class="post-read-more" href="{post.get_absolute_url()}">Read more</a>',
            html=True,
        )


class PostCreateViewTests(TestCase):
    def test_logged_in_user_can_create_a_post(self):
        user = User.objects.create_user(email="person@example.com", password="test-password")
        self.client.force_login(user)

        response = self.client.post(
            reverse("create_post"),
            {"title": "A new post", "content": "Post content"},
        )

        self.assertRedirects(response, reverse("home"))
        post = Post.objects.get()
        self.assertEqual(post.author, user)
        self.assertEqual(post.title, "A new post")
        self.assertEqual(post.content, "Post content")

    def test_logged_out_user_is_redirected_from_post_creation(self):
        response = self.client.get(reverse("create_post"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('create_post')}")


class PostDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="person@example.com",
            password="test-password",
        )
        self.post = Post.objects.create(
            author=self.user,
            title="A post title",
            content="First line\nSecond line",
        )

    def test_post_absolute_url_uses_post_detail_route(self):
        self.assertEqual(self.post.get_absolute_url(), f"/posts/{self.post.pk}/")

    def test_logged_in_user_can_view_post_details(self):
        self.client.force_login(self.user)

        response = self.client.get(self.post.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post"], self.post)
        self.assertContains(response, "A post title")
        self.assertContains(response, "person@example.com")
        self.assertContains(response, date_format(self.post.created_at, "F j, Y"))
        self.assertContains(response, "First line<br>Second line")

    def test_logged_out_user_is_redirected_from_post_details(self):
        response = self.client.get(self.post.get_absolute_url())

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.post.get_absolute_url()}",
        )

    def test_missing_post_returns_not_found(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("post_detail", args=[self.post.pk + 1]))

        self.assertEqual(response.status_code, 404)

    def test_home_post_title_and_comment_link_open_post_page(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("home"))

        self.assertContains(
            response,
            f'<h2><a href="{self.post.get_absolute_url()}">A post title</a></h2>',
            html=True,
        )
        self.assertContains(
            response,
            f'<a class="post-comment-link" href="{self.post.get_absolute_url()}">Comment</a>',
            html=True,
        )
