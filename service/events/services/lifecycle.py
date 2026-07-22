from datetime import datetime

from django.db import transaction
from django.utils import timezone

from events.enums import EventStatus
from events.models import Event


def calculate_event_status(
    *,
    start_at: datetime,
    end_at: datetime,
    cancelled_at: datetime | None,
    now: datetime,
) -> EventStatus:
    if cancelled_at is not None:
        return EventStatus.CANCELLED
    if now < start_at:
        return EventStatus.SCHEDULED
    if now <= end_at:
        return EventStatus.IN_PROGRESS
    return EventStatus.COMPLETED


@transaction.atomic
def reconcile_event_status(*, event: Event, now: datetime | None = None) -> Event:
    effective_now = now or timezone.now()
    expected = calculate_event_status(
        start_at=event.start_at,
        end_at=event.end_at,
        cancelled_at=event.cancelled_at,
        now=effective_now,
    )
    if event.status != expected:
        event.status = expected
        event.save(update_fields=["status", "updated_at"])
    return event


@transaction.atomic
def cancel_event(*, event: Event, now: datetime | None = None) -> Event:
    effective_now = now or timezone.now()
    if event.cancelled_at is None:
        event.cancelled_at = effective_now
        event.save(update_fields=["cancelled_at", "updated_at"])
    return reconcile_event_status(event=event, now=effective_now)


@transaction.atomic
def reactivate_event(*, event: Event, now: datetime | None = None) -> Event:
    effective_now = now or timezone.now()
    if event.cancelled_at is not None:
        event.cancelled_at = None
        event.save(update_fields=["cancelled_at", "updated_at"])
    return reconcile_event_status(event=event, now=effective_now)


@transaction.atomic
def restore_event(*, event: Event, now: datetime | None = None) -> Event:
    effective_now = now or timezone.now()
    if event.deleted_at is not None:
        event.deleted_at = None
        event.save(update_fields=["deleted_at", "updated_at"])
    return reconcile_event_status(event=event, now=effective_now)
