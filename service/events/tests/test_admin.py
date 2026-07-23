from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from events.enums import Audience, EventStatus, EventType
from events.models import Event, EventAudience, EventParticipant
from users.models import User


def _create_user(username: str = "admin_user", **overrides: object) -> User:
    defaults = {
        "email": f"{username}@example.com",
        "password": "secret",
        "onboarding_completed_at": timezone.now(),
    }
    defaults.update(overrides)
    return User.objects.create_user(username=username, **defaults)


def _create_event(creator: User, **overrides: object) -> Event:
    start = timezone.now() + timedelta(days=1)
    defaults = {
        "title": "Test Event",
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


class EventAdminRegistrationTests(TestCase):
    admin_user: User
    regular_user: User
    event: Event
    deleted_event: Event

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = _create_user("superadmin", is_staff=True, is_superuser=True)
        cls.regular_user = _create_user("regular")
        cls.event = _create_event(cls.regular_user)
        cls.deleted_event = _create_event(cls.regular_user, title="Deleted Event")
        cls.deleted_event.soft_delete()

    def setUp(self) -> None:
        self.client.force_login(self.admin_user)

    def test_event_changelist_loads(self) -> None:
        """Admin event list page returns 200."""
        response = self.client.get("/admin/events/event/")
        self.assertEqual(response.status_code, 200)

    def test_event_changelist_includes_deleted_events(self) -> None:
        """all_objects queryset shows soft-deleted events."""
        response = self.client.get("/admin/events/event/")
        self.assertContains(response, "Deleted Event")

    def test_event_photo_inline_present(self) -> None:
        """EventPhoto inline appears on event change page."""
        response = self.client.get(f"/admin/events/event/{self.event.id}/change/")
        # Verbose name plural of EventPhoto is "Fotos do evento"
        self.assertContains(response, "Foto")

    def test_event_changelist_query_count_bounded(self) -> None:
        """Admin list page uses bounded queries.
        Captured exact count: session, user load, contenttype list,
        count for results, count for pagination, then select_related
        queryset, permissions x2, contenttype for admin.
        """
        with self.assertNumQueries(7):
            self.client.get("/admin/events/event/")

    def test_restore_action_restores_deleted_event(self) -> None:
        """The restore action calls restore_event service, clears deleted_at."""
        self.assertTrue(self.deleted_event.deleted_at is not None)
        response = self.client.post(
            "/admin/events/event/",
            {
                "action": "restore_event_action",
                "_selected_action": [str(self.deleted_event.id)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.deleted_event.refresh_from_db()
        self.assertIsNone(self.deleted_event.deleted_at)
