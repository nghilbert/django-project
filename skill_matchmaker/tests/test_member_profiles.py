from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from skill_matchmaker.models import Comment, Post, Skill, User, UserSkill


class MemberProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = User.objects.create_user(email="viewer@example.com")
        cls.member = User.objects.create_user(
            email="member@example.com",
            first_name="Alex",
            last_name="Rivera",
            bio="I enjoy sharing skills.\nLet's learn together.",
        )
        cls.python = Skill.objects.create(name="Python", category="Technology")
        cls.guitar = Skill.objects.create(name="Guitar", category="Music")
        cls.offered = UserSkill.objects.create(
            user=cls.member,
            skill=cls.python,
            skill_type=UserSkill.SkillType.OFFERED,
            level=UserSkill.Level.ADVANCED,
        )
        cls.sought = UserSkill.objects.create(
            user=cls.member,
            skill=cls.guitar,
            skill_type=UserSkill.SkillType.SOUGHT,
            level=UserSkill.Level.BEGINNER,
        )
        viewer_skill = Skill.objects.create(name="Photography", category="Art")
        UserSkill.objects.create(
            user=cls.viewer,
            skill=viewer_skill,
            skill_type=UserSkill.SkillType.OFFERED,
            level=UserSkill.Level.EXPERT,
        )
        UserSkill.objects.create(
            user=cls.viewer,
            skill=viewer_skill,
            skill_type=UserSkill.SkillType.SOUGHT,
        )
        cls.post = Post.objects.create(author=cls.member, title="Learn with me", content="Hi!")
        Comment.objects.create(post=cls.post, author=cls.viewer, content="Count me in.")

    def setUp(self):
        self.client.force_login(self.viewer)
        self.url = reverse("member_profile", args=[self.member.pk])

    def test_profile_shows_member_and_keeps_viewer_in_navigation(self):
        response = self.client.get(self.member.get_absolute_url())

        self.assertEqual(self.url, f"/members/{self.member.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "skill_matchmaker/member_profile.html")
        self.assertEqual(response.context["member"], self.member)
        self.assertEqual(response.context["user"], self.viewer)
        self.assertContains(response, '<h1 id="member-name">Alex Rivera</h1>', html=True)
        self.assertContains(
            response, "<p>I enjoy sharing skills.<br>Let's learn together.</p>", html=True
        )
        self.assertContains(
            response,
            '<span class="nav-user"><span class="nav-user-label">Logged in as</span>'
            "viewer@example.com</span>",
            html=True,
        )

    def test_profile_separates_teaching_and_learning_skills_with_levels(self):
        response = self.client.get(self.url)

        content = response.content.decode()
        offered = content.split('aria-labelledby="offered-heading"')[1].split("</section>")[0]
        sought = content.split('aria-labelledby="sought-heading"')[1].split("</section>")[0]
        self.assertIn("Python", offered)
        self.assertIn("Advanced", offered)
        self.assertNotIn("Guitar", offered)
        self.assertIn("Guitar", sought)
        self.assertIn("Beginner", sought)
        self.assertNotIn("Python", sought)
        self.assertNotContains(response, "Photography")

    def test_logged_out_visitor_is_redirected_to_login_then_profile(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_unknown_member_returns_404(self):
        response = self.client.get(reverse("member_profile", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_profile_is_read_only(self):
        response = self.client.post(self.url, {"bio": "Changed by someone else"})

        self.assertEqual(response.status_code, 405)
        self.member.refresh_from_db()
        self.assertEqual(self.member.bio, "I enjoy sharing skills.\nLet's learn together.")

    def test_member_can_view_their_own_profile(self):
        self.client.force_login(self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["member"], self.member)
        self.assertEqual(response.context["user"], self.member)

    def test_empty_profile_uses_email_and_clear_empty_states(self):
        empty_member = User.objects.create_user(email="new@example.com")

        response = self.client.get(empty_member.get_absolute_url())

        self.assertContains(response, '<h1 id="member-name">new@example.com</h1>', html=True)
        self.assertContains(response, "No bio yet.")
        self.assertContains(response, "No teaching skills added yet.")
        self.assertContains(response, "No learning skills added yet.")
        self.assertContains(response, 'aria-label="No profile picture"')
        self.assertNotContains(response, "<img")

    def test_profile_picture_uses_uploaded_file_url_and_member_name(self):
        self.member.profile_picture = "profile_pictures/alex.png"
        self.member.save(update_fields=["profile_picture"])

        response = self.client.get(self.url)

        self.assertContains(response, f'src="{self.member.profile_picture.url}"')
        self.assertContains(response, 'alt="Profile picture of Alex Rivera"')
        self.assertNotContains(response, 'aria-label="No profile picture"')

    def test_member_content_is_escaped(self):
        self.member.first_name = "<script>alert('name')</script>"
        self.member.bio = "<script>alert('bio')</script>"
        self.member.save(update_fields=["first_name", "bio"])

        response = self.client.get(self.url)

        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_post_authors_link_to_member_from_home_and_post_detail(self):
        for url in (reverse("home"), self.post.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertContains(
                    response,
                    f'<a class="member-link" href="{self.url}">Alex Rivera</a>',
                    html=True,
                )

    def test_comment_author_links_to_their_profile_with_email_fallback(self):
        response = self.client.get(self.post.get_absolute_url())

        self.assertContains(
            response,
            f'<a class="member-link" href="{self.viewer.get_absolute_url()}">'
            "viewer@example.com</a>",
            html=True,
        )

    def test_deleted_member_partial_has_no_broken_link(self):
        content = render_to_string("skill_matchmaker/_member_link.html", {"member": None})

        self.assertEqual(content.strip(), "Deleted user")
        self.assertNotIn("<a", content)

    def test_skill_filters_keep_member_scope_and_load_skill_in_one_query(self):
        for method, expected in (
            ("offered", ("Python", "Advanced")),
            ("sought", ("Guitar", "Beginner")),
        ):
            with self.subTest(method=method), self.assertNumQueries(1):
                skills = getattr(self.member.skills, method)()
                self.assertEqual(
                    [(item.skill.name, item.get_level_display()) for item in skills],
                    [expected],
                )

    def test_skill_filters_work_on_manager_and_chained_querysets(self):
        self.assertQuerySetEqual(
            UserSkill.objects.offered().filter(user=self.member),
            [self.offered],
        )
        self.assertQuerySetEqual(
            UserSkill.objects.filter(user=self.member).sought(),
            [self.sought],
        )

    def test_same_skill_can_appear_in_both_sections_with_different_levels(self):
        UserSkill.objects.create(
            user=self.member,
            skill=self.python,
            skill_type=UserSkill.SkillType.SOUGHT,
            level=UserSkill.Level.EXPERT,
        )

        response = self.client.get(self.url)

        self.assertContains(response, "<span>Python</span>", count=2, html=True)
        self.assertContains(response, '<span class="member-skill-level">Advanced</span>', html=True)
        self.assertContains(response, '<span class="member-skill-level">Expert</span>', html=True)
