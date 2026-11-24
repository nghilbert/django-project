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


class ConnectViewTests(ConnectionTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)
        self.connect_url = reverse("connect", args=[self.bob.pk])

    def test_anonymous_post_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(self.connect_url)
        self.assertRedirects(
            response, f"{reverse('login')}?next={self.connect_url}", fetch_redirect_response=False
        )
        self.assertFalse(Connection.objects.exists())

    def test_get_not_allowed(self):
        response = self.client.get(self.connect_url)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Connection.objects.exists())

    def test_post_creates_pending_request(self):
        response = self.client.post(self.connect_url)
        self.assertRedirects(response, self.bob.get_absolute_url())
        connection = Connection.objects.get()
        self.assertEqual(connection.from_user, self.alice)
        self.assertEqual(connection.to_user, self.bob)
        self.assertEqual(connection.status, Connection.Status.PENDING)

    def test_post_to_self_creates_nothing(self):
        response = self.client.post(reverse("connect", args=[self.alice.pk]))
        self.assertRedirects(response, self.alice.get_absolute_url())
        self.assertFalse(Connection.objects.exists())

    def test_post_twice_creates_one_request(self):
        self.client.post(self.connect_url)
        response = self.client.post(self.connect_url)
        self.assertRedirects(response, self.bob.get_absolute_url())
        self.assertEqual(Connection.objects.count(), 1)

    def test_post_when_they_already_sent_a_request(self):
        existing = Connection.objects.create(from_user=self.bob, to_user=self.alice)
        response = self.client.post(self.connect_url)
        self.assertRedirects(response, self.bob.get_absolute_url())
        self.assertEqual(Connection.objects.count(), 1)
        # Connecting back doesn't accept their request or flip its direction
        existing.refresh_from_db()
        self.assertEqual(existing.from_user, self.bob)
        self.assertEqual(existing.status, Connection.Status.PENDING)

    def test_post_when_already_connected_leaves_connection_alone(self):
        existing = Connection.objects.create(
            from_user=self.bob, to_user=self.alice, status=Connection.Status.ACCEPTED
        )
        response = self.client.post(self.connect_url)
        self.assertRedirects(response, self.bob.get_absolute_url())
        self.assertEqual(Connection.objects.count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.status, Connection.Status.ACCEPTED)

    def test_post_to_nonexistent_member_returns_404(self):
        missing_pk = User.objects.order_by("-pk").first().pk + 1  # type: ignore
        response = self.client.post(reverse("connect", args=[missing_pk]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Connection.objects.exists())

    def test_other_pairs_do_not_block_request(self):
        Connection.objects.create(from_user=self.carol, to_user=self.bob)
        Connection.objects.create(from_user=self.alice, to_user=self.carol)
        self.client.post(self.connect_url)
        self.assertTrue(Connection.objects.filter(from_user=self.alice, to_user=self.bob).exists())


class ProfileConnectionStatusTests(ConnectionTestCase):
    CONNECT_BUTTON = '<button type="submit">Connect</button>'
    REQUEST_SENT = "<p>Request sent</p>"
    SENT_YOU = "<p>Sent you a request</p>"
    CONNECTED = "<p>Connected</p>"
    ALL_STATES = [CONNECT_BUTTON, REQUEST_SENT, SENT_YOU, CONNECTED]

    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)

    def get_profile(self, member):
        response = self.client.get(member.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        return response

    def assertOnlyState(self, response, expected):
        for state in self.ALL_STATES:
            if state == expected:
                self.assertContains(response, state, count=1, html=True)
            else:
                self.assertNotContains(response, state, html=True)

    def test_connect_button_when_no_connection(self):
        response = self.get_profile(self.bob)
        self.assertOnlyState(response, self.CONNECT_BUTTON)
        self.assertContains(response, f'action="{reverse("connect", args=[self.bob.pk])}"')

    def test_connect_button_ignores_other_pairs(self):
        Connection.objects.create(from_user=self.carol, to_user=self.bob)
        self.assertOnlyState(self.get_profile(self.bob), self.CONNECT_BUTTON)

    def test_request_sent(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        self.assertOnlyState(self.get_profile(self.bob), self.REQUEST_SENT)

    def test_sent_you_a_request(self):
        Connection.objects.create(from_user=self.bob, to_user=self.alice)
        self.assertOnlyState(self.get_profile(self.bob), self.SENT_YOU)

    def test_connected_when_accepted(self):
        Connection.objects.create(
            from_user=self.alice, to_user=self.bob, status=Connection.Status.ACCEPTED
        )
        self.assertOnlyState(self.get_profile(self.bob), self.CONNECTED)

    def test_connected_when_they_sent_and_it_was_accepted(self):
        Connection.objects.create(
            from_user=self.bob, to_user=self.alice, status=Connection.Status.ACCEPTED
        )
        self.assertOnlyState(self.get_profile(self.bob), self.CONNECTED)

    def test_own_profile_shows_no_connection_ui(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        Connection.objects.create(from_user=self.carol, to_user=self.alice)
        response = self.get_profile(self.alice)
        self.assertOnlyState(response, None)
        self.assertNotContains(response, reverse("connect", args=[self.alice.pk]))

    def test_button_post_flow_updates_profile(self):
        response = self.client.post(reverse("connect", args=[self.bob.pk]), follow=True)
        self.assertOnlyState(response, self.REQUEST_SENT)


class ConnectionsViewTests(ConnectionTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)
        self.url = reverse("connections")

    def get_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        return response

    def test_anonymous_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse('login')}?next={self.url}", fetch_redirect_response=False
        )

    def test_uses_template(self):
        self.assertTemplateUsed(self.get_page(), "skill_matchmaker/connections.html")

    def test_nav_links_to_page(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, f'href="{self.url}"')

    def test_empty_states(self):
        response = self.get_page()
        self.assertContains(response, "No pending requests.")
        self.assertContains(response, "No connections yet.")

    def test_lists_only_pending_requests_sent_to_you(self):
        received = Connection.objects.create(from_user=self.bob, to_user=self.alice)
        Connection.objects.create(from_user=self.alice, to_user=self.carol)  # Sent by you
        Connection.objects.create(from_user=self.bob, to_user=self.carol)  # Not involving you
        response = self.get_page()
        self.assertEqual(list(response.context["requests"]), [received])
        accept_url = reverse("accept_connection", args=[received.pk])
        self.assertContains(response, f'action="{accept_url}"')
        self.assertContains(response, '<button type="submit">Accept</button>', count=1, html=True)

    def test_accepted_requests_are_not_listed_as_requests(self):
        Connection.objects.create(
            from_user=self.bob, to_user=self.alice, status=Connection.Status.ACCEPTED
        )
        response = self.get_page()
        self.assertEqual(list(response.context["requests"]), [])
        self.assertNotContains(response, '<button type="submit">Accept</button>', html=True)

    def test_lists_connections_in_both_directions(self):
        Connection.objects.create(
            from_user=self.alice, to_user=self.bob, status=Connection.Status.ACCEPTED
        )
        Connection.objects.create(
            from_user=self.carol, to_user=self.alice, status=Connection.Status.ACCEPTED
        )
        response = self.get_page()
        self.assertCountEqual(response.context["connected_users"], [self.bob, self.carol])
        self.assertContains(response, f'href="{self.bob.get_absolute_url()}"')
        self.assertContains(response, f'href="{self.carol.get_absolute_url()}"')

    def test_pending_and_other_pairs_are_not_connections(self):
        Connection.objects.create(from_user=self.alice, to_user=self.bob)
        Connection.objects.create(
            from_user=self.bob, to_user=self.carol, status=Connection.Status.ACCEPTED
        )
        response = self.get_page()
        self.assertEqual(response.context["connected_users"], [])


class AcceptConnectionViewTests(ConnectionTestCase):
    def setUp(self):
        super().setUp()
        self.pending_request = Connection.objects.create(from_user=self.bob, to_user=self.alice)
        self.url = reverse("accept_connection", args=[self.pending_request.pk])
        self.client.force_login(self.alice)

    def assertStillPending(self):
        self.pending_request.refresh_from_db()
        self.assertEqual(self.pending_request.status, Connection.Status.PENDING)

    def test_anonymous_post_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(
            response, f"{reverse('login')}?next={self.url}", fetch_redirect_response=False
        )
        self.assertStillPending()

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertStillPending()

    def test_post_accepts_and_redirects(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("connections"))
        self.pending_request.refresh_from_db()
        self.assertEqual(self.pending_request.status, Connection.Status.ACCEPTED)

    def test_sender_cannot_accept_own_request(self):
        self.client.force_login(self.bob)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertStillPending()

    def test_unrelated_user_cannot_accept(self):
        self.client.force_login(self.carol)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertStillPending()

    def test_already_accepted_returns_404(self):
        self.pending_request.accept()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_request_returns_404(self):
        missing_pk = Connection.objects.order_by("-pk").first().pk + 1  # type: ignore
        response = self.client.post(reverse("accept_connection", args=[missing_pk]))
        self.assertEqual(response.status_code, 404)

    def test_accepting_shows_connection_for_both_users(self):
        response = self.client.post(self.url, follow=True)
        self.assertEqual(list(response.context["requests"]), [])
        self.assertEqual(response.context["connected_users"], [self.bob])

        self.client.force_login(self.bob)
        response = self.client.get(reverse("connections"))
        self.assertEqual(response.context["connected_users"], [self.alice])
