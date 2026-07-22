from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from events.enums import EventStatus, EventType
from events.models import Event
from events.services.lifecycle import (
    calculate_event_status,
    cancel_event,
    reactivate_event,
    reconcile_event_status,
    restore_event,
)
from events.tasks import reconcile_event_statuses
from users.models import User


class CalculateEventStatusTests(TestCase):
    def test_status_is_scheduled_before_start(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now + timedelta(seconds=1),
            end_at=now + timedelta(hours=1),
            cancelled_at=None,
            now=now,
        )
        self.assertEqual(status, EventStatus.SCHEDULED)

    def test_status_is_in_progress_at_exact_end(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now - timedelta(hours=1),
            end_at=now,
            cancelled_at=None,
            now=now,
        )
        self.assertEqual(status, EventStatus.IN_PROGRESS)

    def test_cancelled_overrides_dates(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now - timedelta(days=2),
            end_at=now - timedelta(days=1),
            cancelled_at=now,
            now=now,
        )
        self.assertEqual(status, EventStatus.CANCELLED)

    def test_status_is_completed_after_end(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            cancelled_at=None,
            now=now,
        )
        self.assertEqual(status, EventStatus.COMPLETED)

    def test_status_is_in_progress_before_end(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now - timedelta(minutes=30),
            end_at=now + timedelta(minutes=30),
            cancelled_at=None,
            now=now,
        )
        self.assertEqual(status, EventStatus.IN_PROGRESS)


class ReconcileEventStatusTests(TestCase):
    def setUp(self) -> None:
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_reconcile_updates_from_scheduled_to_in_progress(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now - timedelta(minutes=5),
            end_at=now + timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        reconcile_event_status(event=event, now=now)
        event.refresh_from_db()
        self.assertEqual(event.status, EventStatus.IN_PROGRESS)

    def test_reconcile_updates_from_in_progress_to_completed(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.IN_PROGRESS,
        )
        reconcile_event_status(event=event, now=now)
        event.refresh_from_db()
        self.assertEqual(event.status, EventStatus.COMPLETED)

    def test_reconcile_does_not_update_if_already_correct(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.COMPLETED,
        )
        old_updated_at = event.updated_at
        reconcile_event_status(event=event, now=now)
        event.refresh_from_db()
        self.assertEqual(event.status, EventStatus.COMPLETED)
        self.assertEqual(event.updated_at, old_updated_at)


class CancelEventTests(TestCase):
    def setUp(self) -> None:
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_cancel_event_sets_cancelled_at_and_cancels_status(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        cancel_event(event=event, now=now)
        event.refresh_from_db()
        self.assertIsNotNone(event.cancelled_at)
        self.assertEqual(event.status, EventStatus.CANCELLED)

    def test_cancel_event_is_idempotent(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        cancel_event(event=event, now=now)
        first_cancelled_at = event.cancelled_at
        cancel_event(event=event, now=now)
        event.refresh_from_db()
        self.assertEqual(event.cancelled_at, first_cancelled_at)
        self.assertEqual(event.status, EventStatus.CANCELLED)


class ReactivateEventTests(TestCase):
    def setUp(self) -> None:
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_reactivate_event_clears_cancelled_at_and_reconciles(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.CANCELLED,
            cancelled_at=now,
        )
        reactivate_event(event=event, now=now)
        event.refresh_from_db()
        self.assertIsNone(event.cancelled_at)
        self.assertEqual(event.status, EventStatus.SCHEDULED)

    def test_reactivate_event_is_idempotent(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.CANCELLED,
            cancelled_at=now,
        )
        reactivate_event(event=event, now=now)
        event.refresh_from_db()
        self.assertIsNone(event.cancelled_at)
        self.assertEqual(event.status, EventStatus.SCHEDULED)
        # Call again — should be fine
        reactivate_event(event=event, now=now)
        event.refresh_from_db()
        self.assertIsNone(event.cancelled_at)
        self.assertEqual(event.status, EventStatus.SCHEDULED)


class RestoreEventTests(TestCase):
    def setUp(self) -> None:
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_restore_event_clears_deleted_at_and_reconciles(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        event.soft_delete()
        event.refresh_from_db()
        self.assertIsNotNone(event.deleted_at)

        restore_event(event=event, now=now)
        event.refresh_from_db()
        self.assertIsNone(event.deleted_at)
        self.assertEqual(event.status, EventStatus.SCHEDULED)

    def test_restore_event_is_idempotent(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        event.soft_delete()
        restore_event(event=event, now=now)
        restore_event(event=event, now=now)
        event.refresh_from_db()
        self.assertIsNone(event.deleted_at)
        self.assertEqual(event.status, EventStatus.SCHEDULED)


class ReconcileEventStatusesTaskTests(TestCase):
    def setUp(self) -> None:
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_task_updates_overdue_events_and_returns_count(self) -> None:
        now = timezone.now()
        # One event that should be IN_PROGRESS
        event1 = Event.objects.create(
            title="In progress",
            start_at=now - timedelta(minutes=5),
            end_at=now + timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        # One event that should be COMPLETED
        event2 = Event.objects.create(
            title="Completed",
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.IN_PROGRESS,
        )
        # One deleted event that should be skipped
        event3 = Event.objects.create(
            title="Deleted",
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.IN_PROGRESS,
        )
        event3.soft_delete()

        count = reconcile_event_statuses()
        self.assertEqual(count, 2)
        event1.refresh_from_db()
        event2.refresh_from_db()
        self.assertEqual(event1.status, EventStatus.IN_PROGRESS)
        self.assertEqual(event2.status, EventStatus.COMPLETED)
        # Deleted event should still have old status
        event3.refresh_from_db()
        self.assertEqual(event3.status, EventStatus.IN_PROGRESS)
        self.assertIsNotNone(event3.deleted_at)

    def test_task_is_idempotent(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.IN_PROGRESS,
        )
        reconcile_event_statuses()
        event.refresh_from_db()
        self.assertEqual(event.status, EventStatus.COMPLETED)

        # Second call should report 0 updates
        count = reconcile_event_statuses()
        self.assertEqual(count, 0)
