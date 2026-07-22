from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.enums import Audience, EventStatus, EventType
from events.models import Event, EventAudience, EventParticipant
from users.models import User


def _create_user(username: str = "user1", **overrides) -> User:
    defaults = {
        "email": f"{username}@example.com",
        "password": "secret",
        "onboarding_completed_at": timezone.now(),
    }
    defaults.update(overrides)
    return User.objects.create_user(username=username, **defaults)


def _make_event_data(**overrides) -> dict:
    start = timezone.now() + timedelta(days=30)
    defaults = {
        "title": "Test Event",
        "description": "A test event",
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=3)).isoformat(),
        "type": EventType.CABULOUS,
        "audiences": [Audience.ILUMINADOS, Audience.VOYEURS],
    }
    defaults.update(overrides)
    return defaults


def _create_event(creator, **overrides) -> Event:
    start = timezone.now() + timedelta(days=1)
    defaults = {
        "title": "Existing Event",
        "start_at": start,
        "end_at": start + timedelta(hours=2),
        "type": EventType.CABULOUS,
        "creator": creator,
        "status": EventStatus.SCHEDULED,
    }
    defaults.update(overrides)
    event = Event.objects.create(**defaults)
    EventAudience.objects.create(event=event, audience=Audience.ILUMINADOS)
    EventParticipant.objects.create(event=event, user=creator)
    return event


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class EventCreateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("creator")
        self.url = "/api/events/"

    def test_onboarded_user_creates_event_and_becomes_participant(self) -> None:
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, _make_event_data(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(id=response.data["id"])
        self.assertEqual(event.creator, self.user)
        self.assertTrue(event.participants.filter(user=self.user).exists())

    def test_create_with_location(self) -> None:
        self.client.force_authenticate(self.user)
        data = _make_event_data(
            location={
                "name": "Bar do Ze",
                "address": "Rua A, 123",
                "latitude": "-23.550520",
                "longitude": "-46.633308",
            }
        )
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(id=response.data["id"])
        self.assertEqual(event.location.name, "Bar do Ze")

    def test_create_empty_audiences_list_rejected(self) -> None:
        self.client.force_authenticate(self.user)
        data = _make_event_data(audiences=[])
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_audiences_rejected(self) -> None:
        self.client.force_authenticate(self.user)
        data = _make_event_data()
        del data["audiences"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_type_rejected(self) -> None:
        self.client.force_authenticate(self.user)
        data = _make_event_data(type="INVALID")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_end_before_start_rejected(self) -> None:
        self.client.force_authenticate(self.user)
        start = timezone.now() + timedelta(days=30)
        data = _make_event_data(
            start_at=start.isoformat(),
            end_at=(start - timedelta(hours=1)).isoformat(),
        )
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_create_returns_401(self) -> None:
        response = self.client.post(self.url, _make_event_data(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pending_onboarding_returns_403(self) -> None:
        pending = _create_user("pending", onboarding_completed_at=None)
        self.client.force_authenticate(pending)
        response = self.client.post(self.url, _make_event_data(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# List / Retrieve
# ---------------------------------------------------------------------------


class EventListTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("viewer")
        self.other = _create_user("other")
        self.url = "/api/events/"
        self.client.force_authenticate(self.user)

    def test_list_returns_200(self) -> None:
        _create_event(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_list_includes_other_users_events(self) -> None:
        _create_event(self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 1)

    def test_retrieve_returns_200(self) -> None:
        event = _create_event(self.user)
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(event.id))


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class EventUpdateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.staff = _create_user("staff", is_staff=True)
        self.client.force_authenticate(self.creator)

    def test_creator_can_patch(self) -> None:
        event = _create_event(self.creator)
        response = self.client.patch(
            f"/api/events/{event.id}/", {"title": "Updated"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.title, "Updated")

    def test_other_user_cannot_patch(self) -> None:
        event = _create_event(self.creator)
        self.client.force_authenticate(self.other)
        response = self.client.patch(
            f"/api/events/{event.id}/", {"title": "Hacked"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_patch(self) -> None:
        event = _create_event(self.creator)
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            f"/api/events/{event.id}/", {"title": "Staff Edit"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_replaces_audiences_when_provided(self) -> None:
        event = _create_event(self.creator)
        self.assertEqual(event.audiences.count(), 1)
        response = self.client.patch(
            f"/api/events/{event.id}/",
            {"audiences": [Audience.VOYEURS, Audience.ELETRONICOS]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.audiences.count(), 2)

    def test_update_preserves_audiences_when_not_provided(self) -> None:
        event = _create_event(self.creator)
        self.assertEqual(event.audiences.count(), 1)
        response = self.client.patch(
            f"/api/events/{event.id}/", {"title": "Keep audiences"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.audiences.count(), 1)


# ---------------------------------------------------------------------------
# Delete (soft)
# ---------------------------------------------------------------------------


class EventDeleteTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.client.force_authenticate(self.creator)

    def test_creator_can_delete(self) -> None:
        event = _create_event(self.creator)
        response = self.client.delete(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Event.all_objects.filter(id=event.id).exists())
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_other_user_cannot_delete(self) -> None:
        event = _create_event(self.creator)
        self.client.force_authenticate(self.other)
        response = self.client.delete(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Cancel / Reactivate
# ---------------------------------------------------------------------------


class EventCancelReactivateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.client.force_authenticate(self.creator)

    def test_creator_can_cancel(self) -> None:
        event = _create_event(self.creator)
        response = self.client.post(f"/api/events/{event.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.status, EventStatus.CANCELLED)

    def test_other_user_cannot_cancel(self) -> None:
        event = _create_event(self.creator)
        self.client.force_authenticate(self.other)
        response = self.client.post(f"/api/events/{event.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_can_reactivate(self) -> None:
        event = _create_event(
            self.creator,
            status=EventStatus.CANCELLED,
            cancelled_at=timezone.now(),
        )
        response = self.client.post(f"/api/events/{event.id}/reactivate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertIsNone(event.cancelled_at)

    def test_other_user_cannot_reactivate(self) -> None:
        event = _create_event(
            self.creator,
            status=EventStatus.CANCELLED,
            cancelled_at=timezone.now(),
        )
        self.client.force_authenticate(self.other)
        response = self.client.post(f"/api/events/{event.id}/reactivate/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancelled_event_invisible_in_active_list(self) -> None:
        _create_event(self.creator)
        cancelled = _create_event(self.creator, title="Cancelled")
        self.client.post(f"/api/events/{cancelled.id}/cancel/")
        response = self.client.get("/api/events/")
        titles = [e["title"] for e in response.data["results"]]
        self.assertNotIn("Cancelled", titles)

    def test_reactivated_event_visible_in_active_list(self) -> None:
        cancelled = _create_event(
            self.creator,
            title="Was cancelled",
            status=EventStatus.CANCELLED,
            cancelled_at=timezone.now(),
        )
        self.client.post(f"/api/events/{cancelled.id}/reactivate/")
        response = self.client.get("/api/events/")
        titles = [e["title"] for e in response.data["results"]]
        self.assertIn("Was cancelled", titles)


# ---------------------------------------------------------------------------
# Restore (staff only)
# ---------------------------------------------------------------------------


class EventRestoreTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.staff = _create_user("staff", is_staff=True)
        self.creator = _create_user("creator")
        self.other = _create_user("other")

    def test_staff_can_restore(self) -> None:
        event = _create_event(self.creator)
        event.soft_delete()
        self.client.force_authenticate(self.staff)
        response = self.client.post(f"/api/events/{event.id}/restore/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertIsNone(event.deleted_at)

    def test_creator_cannot_restore(self) -> None:
        event = _create_event(self.creator)
        event.soft_delete()
        self.client.force_authenticate(self.creator)
        response = self.client.post(f"/api/events/{event.id}/restore/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_user_cannot_restore(self) -> None:
        event = _create_event(self.creator)
        event.soft_delete()
        self.client.force_authenticate(self.other)
        response = self.client.post(f"/api/events/{event.id}/restore/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_restore_404_for_nonexistent_event(self) -> None:
        self.client.force_authenticate(self.staff)
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.post(f"/api/events/{fake_id}/restore/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


class EventPermissionTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("user1")
        self.other = _create_user("user2")
        self.staff = _create_user("staff", is_staff=True)

    def test_anonymous_list_returns_401(self) -> None:
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pending_onboarding_list_returns_403(self) -> None:
        pending = _create_user("pending", onboarding_completed_at=None)
        self.client.force_authenticate(pending)
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_any_onboarded_user_can_list(self) -> None:
        _create_event(self.other)
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_any_onboarded_user_can_retrieve(self) -> None:
        event = _create_event(self.other)
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


class EventFilterTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("user1")
        self.other = _create_user("user2")
        self.client.force_authenticate(self.user)

        now = timezone.now()

        self.event1 = _create_event(
            self.user,
            title="Beach Party",
            start_at=now + timedelta(days=5),
            end_at=now + timedelta(days=5, hours=4),
            type=EventType.CLUB,
        )
        # Replace default ILUMINADOS audience with VOYEURS
        EventAudience.objects.filter(event=self.event1).delete()
        EventAudience.objects.create(event=self.event1, audience=Audience.VOYEURS)

        self.event2 = _create_event(
            self.user,
            title="Birthday Bash",
            start_at=now + timedelta(days=10),
            end_at=now + timedelta(days=10, hours=3),
            type=EventType.BIRTHDAY,
        )
        # Replace default ILUMINADOS with OTHERS so only event3 has ILUMINADOS
        EventAudience.objects.filter(event=self.event2).delete()
        EventAudience.objects.create(event=self.event2, audience=Audience.OTHERS)

        self.event3 = _create_event(
            self.other,
            title="Workshop Talk",
            start_at=now + timedelta(days=2),
            end_at=now + timedelta(days=2, hours=2),
            type=EventType.CASUAL_HANGOUT,
        )
        # event3 already has ILUMINADOS from _create_event, no extra create needed

    def test_filter_starts_from(self) -> None:
        now = timezone.now()
        response = self.client.get(
            "/api/events/", {"starts_from": (now + timedelta(days=9)).date().isoformat()}
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.event2.id))

    def test_filter_starts_until(self) -> None:
        now = timezone.now()
        response = self.client.get(
            "/api/events/", {"starts_until": (now + timedelta(days=3)).date().isoformat()}
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.event3.id))

    def test_filter_status(self) -> None:
        self.event1.cancelled_at = timezone.now()
        self.event1.status = EventStatus.CANCELLED
        self.event1.save(update_fields=["status", "cancelled_at", "updated_at"])
        response = self.client.get("/api/events/", {"status": EventStatus.CANCELLED})
        self.assertEqual(response.data["count"], 1)

    def test_filter_type(self) -> None:
        response = self.client.get("/api/events/", {"type": EventType.BIRTHDAY})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.event2.id))

    def test_filter_audience(self) -> None:
        response = self.client.get("/api/events/", {"audience": Audience.ILUMINADOS})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.event3.id))

    def test_filter_participant(self) -> None:
        response = self.client.get("/api/events/", {"participant": str(self.user.id)})
        self.assertEqual(response.data["count"], 2)

    def test_filter_creator(self) -> None:
        response = self.client.get("/api/events/", {"creator": str(self.user.id)})
        self.assertEqual(response.data["count"], 2)

    def test_search_title(self) -> None:
        response = self.client.get("/api/events/", {"search": "Beach"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.event1.id))

    def test_search_description(self) -> None:
        self.event1.description = "Sunset cocktails"
        self.event1.save(update_fields=["description", "updated_at"])
        response = self.client.get("/api/events/", {"search": "Sunset"})
        self.assertEqual(response.data["count"], 1)

    def test_ordering_start_at(self) -> None:
        response = self.client.get("/api/events/", {"ordering": "start_at"})
        ids = [e["id"] for e in response.data["results"]]
        self.assertEqual(ids[0], str(self.event3.id))


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class EventPaginationTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("creator")
        self.client.force_authenticate(self.user)

    def test_pagination_page_size_20(self) -> None:
        for i in range(25):
            _create_event(
                self.user,
                title=f"Event {i}",
                start_at=timezone.now() + timedelta(days=i),
                end_at=timezone.now() + timedelta(days=i, hours=1),
            )
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])

        response2 = self.client.get(response.data["next"])
        self.assertEqual(len(response2.data["results"]), 5)
        self.assertIsNone(response2.data["next"])


# ---------------------------------------------------------------------------
# N+1 prevention
# ---------------------------------------------------------------------------


class EventQueryCountTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("creator")
        self.client.force_authenticate(self.user)

    def test_list_query_count_is_bounded(self) -> None:
        for i in range(10):
            _create_event(
                self.user,
                title=f"Event {i}",
                start_at=timezone.now() + timedelta(days=i),
                end_at=timezone.now() + timedelta(days=i, hours=1),
            )
        with self.assertNumQueries(5):
            response = self.client.get("/api/events/")
        self.assertEqual(len(response.data["results"]), 10)


# ---------------------------------------------------------------------------
# Options endpoint
# ---------------------------------------------------------------------------


class EventOptionsTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("user1")
        self.client.force_authenticate(self.user)

    def test_options_returns_enums(self) -> None:
        response = self.client.get("/api/events/options/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("types", response.data)
        self.assertIn("audiences", response.data)
        self.assertIn("statuses", response.data)
        # Each entry should have value and label
        first_type = response.data["types"][0]
        self.assertIn("value", first_type)
        self.assertIn("label", first_type)
        # Types should include color
        self.assertIn("color", first_type)


# ---------------------------------------------------------------------------
# Read serializer fields
# ---------------------------------------------------------------------------


class EventReadSerializerTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("creator")
        self.client.force_authenticate(self.user)

    def test_read_includes_audiences(self) -> None:
        event = _create_event(self.user)
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertIn("audiences", response.data)
        self.assertIsInstance(response.data["audiences"], list)
        self.assertGreater(len(response.data["audiences"]), 0)

    def test_read_includes_participants_count(self) -> None:
        event = _create_event(self.user)
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertIn("participants_count", response.data)
        self.assertEqual(response.data["participants_count"], 1)

    def test_read_includes_type_color(self) -> None:
        event = _create_event(self.user)
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertIn("type_color", response.data)
        self.assertEqual(response.data["type_color"], "#8E44AD")

    def test_read_includes_status(self) -> None:
        event = _create_event(self.user)
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.data["status"], EventStatus.SCHEDULED)
