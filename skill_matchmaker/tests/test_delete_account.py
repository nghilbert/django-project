from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from skill_matchmaker.models import Comment, Post, Skill, User, UserSkill


class DeleteAccountTests(TestCase):
    password = "CampusPractice847!"

    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password=self.password)
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse("delete_account"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('delete_account')}",
        )

    def test_confirmation_page_has_password_field_warning_and_cancel_link(self):
        response = self.client.get(reverse("delete_account"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="password"')
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, "Warning: This action cannot be undone")
        self.assertContains(
            response,
            "permanently delete your posts, comments, reactions, and skills",
        )
        self.assertContains(response, f'href="{reverse("account_settings")}">Cancel</a>')

    def test_incorrect_password_does_not_delete_or_log_out_user(self):
        response = self.client.post(reverse("delete_account"), {"password": "wrong"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect password.")
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_correct_password_deletes_account_and_related_content(self):
        skill = Skill.objects.create(name="Guitar", category="Music")
        UserSkill.objects.create(user=self.user, skill=skill)
        post = Post.objects.create(author=self.user, title="Post", content="Content")
        Comment.objects.create(author=self.user, post=post, content="Comment")

        response = self.client.post(reverse("delete_account"), {"password": self.password})

        self.assertRedirects(response, reverse("account_deleted"))
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
        self.assertFalse(Comment.objects.exists())
        self.assertFalse(UserSkill.objects.exists())
        self.assertNotIn("_auth_user_id", self.client.session)

        deleted_response = self.client.get(reverse("account_deleted"))
        self.assertContains(deleted_response, "Your account was deleted")

    def test_deleting_account_removes_profile_picture(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.user.profile_picture.save(
                "profile.png",
                SimpleUploadedFile("profile.png", b"profile image"),
            )
            picture_path = Path(media_root) / self.user.profile_picture.name
            self.assertTrue(picture_path.exists())

            self.client.post(reverse("delete_account"), {"password": self.password})

            self.assertFalse(picture_path.exists())
