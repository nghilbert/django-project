from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from skill_matchmaker.models import Connection, User


class ConnectionTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="alice@example.com", password="test-password")
        self.bob = User.objects.create_user(email="bob@example.com", password="test-password")
        self.carol = User.objects.create_user(email="carol@example.com", password="test-password")


class ConnectionModelTests(ConnectionTestCase):
    def test_defaults_to_pending(self):
        connection = Connection.objects.create(from_user=self.alice, to_user=self.bob)
        self.assertEqual(connection.status, Connection.Status.PENDING)
        self.assertIsNotNone(connection.created_at)

    def test_related_names(self):
        connection = Connection.objects.create(from_user=self.alice, to_user=self.bob)
        self.assertEqual(list(self.alice.connections_sent.all()), [connection])  # type: ignore
        self.assertEqual(list(self.bob.connections_received.all()), [connection])  # type: ignore

    def test_deleting_a_user_deletes_their_connections(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        Connection.objects.create(from_user=self.carol, to_user=self.alice)
        self.alice.delete()
        self.assertFalse(Connection.objects.exists())


class ConnectionConstraintTests(ConnectionTestCase):
    def test_blocks_duplicate_in_same_direction(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Connection.objects.create(from_user=self.alice, to_user=self.bob)

    def test_blocks_duplicate_in_reverse_direction(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Connection.objects.create(from_user=self.bob, to_user=self.alice)

    def test_allows_other_pairs(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        Connection.objects.create(from_user=self.alice, to_user=self.carol)
        Connection.objects.create(from_user=self.carol, to_user=self.bob)
        self.assertEqual(Connection.objects.count(), 3)

    def test_blocks_self_connection(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Connection.objects.create(from_user=self.alice, to_user=self.alice)

    def test_full_clean_reports_duplicate_pair(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        with self.assertRaisesMessage(ValidationError, "These users already have a connection"):
            Connection(from_user=self.bob, to_user=self.alice).full_clean()

    def test_full_clean_reports_self_connection(self):
        with self.assertRaisesMessage(ValidationError, "User can't connect to themselves."):
            Connection(from_user=self.alice, to_user=self.alice).full_clean()


class ConnectionQuerySetTests(ConnectionTestCase):
    def setUp(self):
        super().setUp()
        self.alice_bob = Connection.objects.create(from_user=self.alice, to_user=self.bob)
        self.carol_alice = Connection.objects.create(
            from_user=self.carol, to_user=self.alice, status=Connection.Status.ACCEPTED
        )

    def test_between_matches_either_direction(self):
        self.assertEqual(list(Connection.objects.between(self.alice, self.bob)), [self.alice_bob])
        self.assertEqual(list(Connection.objects.between(self.bob, self.alice)), [self.alice_bob])

    def test_between_unconnected_users_is_empty(self):
        self.assertFalse(Connection.objects.between(self.bob, self.carol).exists())

    def test_involving_matches_sent_and_received(self):
        self.assertCountEqual(
            Connection.objects.involving(self.alice), [self.alice_bob, self.carol_alice]
        )
        self.assertEqual(list(Connection.objects.involving(self.bob)), [self.alice_bob])

    def test_pending_and_accepted(self):
        self.assertEqual(list(Connection.objects.pending()), [self.alice_bob])
        self.assertEqual(list(Connection.objects.accepted()), [self.carol_alice])

    def test_methods_chain(self):
        self.assertEqual(
            list(Connection.objects.involving(self.alice).accepted()), [self.carol_alice]
        )
        self.assertFalse(Connection.objects.involving(self.bob).accepted().exists())


class ConnectionMethodTests(ConnectionTestCase):
    def setUp(self):
        super().setUp()
        self.connection = Connection.objects.create(from_user=self.alice, to_user=self.bob)

    def test_accept_saves_accepted_status(self):
        self.connection.accept()
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, Connection.Status.ACCEPTED)

    def test_deny_deletes_request(self):
        self.connection.deny()
        self.assertFalse(Connection.objects.exists())

    def test_deny_lets_users_connect_again(self):
        self.connection.deny()
        Connection.objects.create(from_user=self.bob, to_user=self.alice)
        self.assertEqual(Connection.objects.count(), 1)

    def test_other_user(self):
        self.assertEqual(self.connection.other_user(self.alice), self.bob)
        self.assertEqual(self.connection.other_user(self.bob), self.alice)

    def test_str(self):
        self.assertEqual(str(self.connection), "alice@example.com -> bob@example.com (Pending)")


class ConnectionAdminTests(ConnectionTestCase):
    def test_changelist_loads(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        admin_user = User.objects.create_superuser(
            email="admin@example.com", password="test-password"
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:skill_matchmaker_connection_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice@example.com")
