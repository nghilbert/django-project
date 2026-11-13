from django.test import TestCase
from django.urls import reverse
from django.utils.formats import date_format

from skill_matchmaker.models import Comment, Post, Reaction, User


class DeletePostTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(email="author@example.com", password="test-pass")
        self.other_user = User.objects.create_user(email="other@example.com", password="test-pass")
        self.post = Post.objects.create(
            author=self.author,
            title="A post title",
            content="Post content",
        )
        self.delete_url = reverse("delete_post", args=[self.post.pk])

    def test_logged_out_user_is_redirected_from_delete_page(self):
        response = self.client.get(self.delete_url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.delete_url}",
        )

    def test_author_can_open_confirmation_page_without_deleting_post(self):
        self.client.force_login(self.author)

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete this post?")
        self.assertContains(response, "A post title")
        self.assertContains(response, "author@example.com")
        self.assertContains(response, date_format(self.post.created_at, "F j, Y"))
        self.assertContains(response, date_format(self.post.updated_at, "F j, Y"))
        self.assertNotContains(response, "Post content")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(
            response, f'href="{reverse("post_detail", args=[self.post.pk])}">Cancel</a>'
        )
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_non_author_gets_not_found(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_missing_post_returns_not_found(self):
        self.client.force_login(self.author)

        response = self.client.get(reverse("delete_post", args=[self.post.pk + 1]))

        self.assertEqual(response.status_code, 404)

    def test_confirming_deletion_removes_post_and_related_content(self):
        Comment.objects.create(
            author=self.author,
            post=self.post,
            content="A comment",
        )
        Reaction.objects.create(
            user=self.author,
            post=self.post,
            emoji=Reaction.Emoji.HEART,
        )
        self.client.force_login(self.author)

        response = self.client.post(self.delete_url)

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
        self.assertFalse(Comment.objects.exists())
        self.assertFalse(Reaction.objects.exists())

    def test_delete_link_is_only_shown_to_post_author(self):
        self.client.force_login(self.author)

        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(
            response,
            f'<a class="button post-detail-delete" href="{self.delete_url}">Delete page</a>',
            html=True,
        )

        self.client.force_login(self.other_user)
        response = self.client.get(self.post.get_absolute_url())

        self.assertNotContains(response, self.delete_url)
