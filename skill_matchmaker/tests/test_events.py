from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from skill_matchmaker.models import CampusLocation, Event, Post, Skill, User


class EventTestCase(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(email="author@example.com", password="test-password")
        self.skill = Skill.objects.create(name="Guitar", category="Music")
        self.location = CampusLocation.objects.create(building="Milner Library", room="201")
        self.starts_at = timezone.now() + timedelta(days=7)

    def make_event(self, **kwargs):
        fields = {
            "author": self.author,
            "title": "Guitar basics",
            "content": "Bring a guitar if you have one.",
            "starts_at": self.starts_at,
            "skill": self.skill,
            "location": self.location,
        }
        fields.update(kwargs)
        return Event.objects.create(**fields)


class CampusLocationTests(EventTestCase):
    def test_str(self):
        self.assertEqual(str(self.location), "Milner Library 201")

    def test_blocks_duplicate_building_and_room(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CampusLocation.objects.create(building="Milner Library", room="201")

    def test_allows_same_building_with_other_room(self):
        CampusLocation.objects.create(building="Milner Library", room="202")
        self.assertEqual(CampusLocation.objects.count(), 2)

    def test_allows_same_room_in_other_building(self):
        CampusLocation.objects.create(building="Schroeder Hall", room="201")
        self.assertEqual(CampusLocation.objects.count(), 2)

    def test_full_clean_reports_duplicate(self):
        with self.assertRaisesMessage(ValidationError, "This building and room already exist."):
            CampusLocation(building="Milner Library", room="201").full_clean()

    def test_ordered_by_building_then_room(self):
        schroeder = CampusLocation.objects.create(building="Schroeder Hall", room="130")
        milner_105 = CampusLocation.objects.create(building="Milner Library", room="105")
        self.assertEqual(list(CampusLocation.objects.all()), [milner_105, self.location, schroeder])


class EventConstraintTests(EventTestCase):
    def test_allows_location_only(self):
        event = self.make_event()
        self.assertEqual(event.location, self.location)
        self.assertEqual(event.meeting_link, "")

    def test_allows_meeting_link_only(self):
        event = self.make_event(location=None, meeting_link="https://example.com/meet")
        self.assertIsNone(event.location)

    def test_allows_location_and_meeting_link(self):
        event = self.make_event(meeting_link="https://example.com/meet")
        self.assertEqual(event.location, self.location)
        self.assertEqual(event.meeting_link, "https://example.com/meet")

    def test_blocks_no_location_or_link(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_event(location=None)

    def test_full_clean_reports_no_location_or_link(self):
        event = Event(
            author=self.author,
            title="Guitar basics",
            content="Bring a guitar if you have one.",
            starts_at=self.starts_at,
            skill=self.skill,
        )
        with self.assertRaisesMessage(ValidationError, "Add a location or a meeting link."):
            event.full_clean()


class EventModelTests(EventTestCase):
    def test_event_is_also_a_post(self):
        event = self.make_event()
        post = Post.objects.get(pk=event.pk)
        self.assertEqual(post.title, "Guitar basics")
        self.assertEqual(post.event, event)  # type: ignore

    def test_str_uses_title(self):
        self.assertEqual(str(self.make_event()), "Guitar basics")

    def test_related_names(self):
        event = self.make_event()
        self.assertEqual(list(self.skill.events.all()), [event])  # type: ignore
        self.assertEqual(list(self.location.events.all()), [event])  # type: ignore
        self.assertEqual(list(self.author.posts.all()), [event.post_ptr])  # type: ignore

    def test_cannot_delete_skill_used_by_event(self):
        self.make_event()
        with self.assertRaises(ProtectedError):
            self.skill.delete()
        self.assertTrue(Skill.objects.filter(pk=self.skill.pk).exists())

    def test_cannot_delete_location_used_by_event(self):
        self.make_event()
        with self.assertRaises(ProtectedError):
            self.location.delete()
        self.assertTrue(CampusLocation.objects.filter(pk=self.location.pk).exists())

    def test_can_delete_unused_location(self):
        self.location.delete()
        self.assertFalse(CampusLocation.objects.exists())

    def test_deleting_author_deletes_their_events(self):
        self.make_event()
        self.author.delete()
        self.assertFalse(Event.objects.exists())
        self.assertFalse(Post.objects.exists())

    def test_deleting_post_deletes_event(self):
        event = self.make_event()
        Post.objects.get(pk=event.pk).delete()
        self.assertFalse(Event.objects.exists())

    def test_post_page_shows_event(self):
        event = self.make_event()
        self.client.force_login(self.author)
        response = self.client.get(event.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guitar basics")

        Post.objects.get(pk=event.pk).delete()
        self.assertFalse(Event.objects.exists())


class EventAdminTests(EventTestCase):
    def setUp(self):
        super().setUp()
        admin_user = User.objects.create_superuser(
            email="admin@example.com", password="test-password"
        )
        self.client.force_login(admin_user)

    def test_event_changelist_loads(self):
        self.make_event()
        response = self.client.get(reverse("admin:skill_matchmaker_event_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guitar basics")

    def test_campus_location_changelist_loads(self):
        response = self.client.get(reverse("admin:skill_matchmaker_campuslocation_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Milner Library")
