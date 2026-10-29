from django.test import TestCase
from django.urls import reverse

from skill_matchmaker.forms.accounts import RegistrationForm
from skill_matchmaker.models import User


class RegistrationTests(TestCase):
    def setUp(self):
        self.data = {
            "email": "Student@ILSTU.EDU",
            "first_name": "Test",
            "last_name": "Student",
            "password1": "CampusPractice847!",
            "password2": "CampusPractice847!",
        }

    def test_registration_page(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")
        for field in self.data:
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')

    def test_registration_creates_inactive_user(self):
        response = self.client.post(reverse("register"), self.data)
        self.assertRedirects(response, reverse("check_email"))
        self.assertContains(self.client.get(reverse("check_email")), "Check your email")
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(email="student@ilstu.edu")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "Student")
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password(self.data["password1"]))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_rejects_invalid_email(self):
        for email in [
            "student@gmail.com",
            "student@sub.ilstu.edu",
            "student@ilstu.edu.example.com",
            "not-an-email",
        ]:
            with self.subTest(email=email):
                self.data["email"] = email
                response = self.client.post(reverse("register"), self.data)
                self.assertEqual(response.status_code, 200)
                self.assertIn("email", response.context["form"].errors)
                self.assertFalse(User.objects.exists())

    def test_rejects_duplicate_email_in_any_case(self):
        User.objects.create_user(email="student@ilstu.edu", password="ExistingPassword847!")
        for email in ["student@ilstu.edu", "Student@ILSTU.EDU", "STUDENT@ilstu.edu"]:
            with self.subTest(email=email):
                self.data["email"] = email
                response = self.client.post(reverse("register"), self.data)
                self.assertEqual(response.status_code, 200)
                self.assertIn("email", response.context["form"].errors)
                self.assertEqual(User.objects.count(), 1)

    def test_requires_all_fields(self):
        for field in self.data:
            with self.subTest(field=field):
                data = self.data.copy()
                data[field] = ""
                response = self.client.post(reverse("register"), data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertFalse(User.objects.exists())

    def test_rejects_mismatched_passwords(self):
        self.data["password2"] = "DifferentPassword847!"
        response = self.client.post(reverse("register"), self.data)
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(User.objects.exists())

    def test_rejects_weak_password(self):
        self.data["password1"] = "123"
        self.data["password2"] = "123"
        response = self.client.post(reverse("register"), self.data)
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(User.objects.exists())

    def test_save_without_commit(self):
        form = RegistrationForm(self.data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(commit=False)
        self.assertIsNone(user.pk)
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, "student@ilstu.edu")
        self.assertTrue(user.check_password(self.data["password1"]))
        self.assertFalse(User.objects.exists())

    def test_inactive_user_cannot_log_in(self):
        self.client.post(reverse("register"), self.data)
        response = self.client.post(
            reverse("login"),
            {"username": "STUDENT@ILSTU.EDU", "password": self.data["password1"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your account is not verified yet.")
        self.assertNotIn("_auth_user_id", self.client.session)
