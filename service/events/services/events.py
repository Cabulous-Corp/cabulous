from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from events.enums import EventStatus
from events.models import Event, EventAudience, EventLocation, EventParticipant
from events.services.lifecycle import reconcile_event_status
from events.services.relations import add_participants

if TYPE_CHECKING:
    from users.models import User

_UNSET = object()  # ponytail: sentinel for "location key not in payload"


def _build_location(event: Event, location_data: dict[str, object]) -> None:
    EventLocation.objects.create(  # type: ignore[misc]
        event=event,
        name=location_data.get("name", ""),
        address=location_data["address"],
        latitude=location_data["latitude"],
        longitude=location_data["longitude"],
    )


@transaction.atomic
def create_event(
    *,
    creator: User,
    title: str,
    description: str,
    start_at: object,
    end_at: object,
    event_type: str,
    audiences: list[str],
    location: dict[str, object] | None = None,
    host_ids: list[str] | None = None,
) -> Event:
    event = Event.objects.create(  # type: ignore[misc]
        creator=creator,
        title=title,
        description=description,
        start_at=start_at,
        end_at=end_at,
        type=event_type,
        status=EventStatus.SCHEDULED,
    )
    EventAudience.objects.bulk_create([EventAudience(event=event, audience=a) for a in audiences])
    if location is not None:
        _build_location(event, location)
    EventParticipant.objects.create(event=event, user=creator)
    if host_ids:
        event.hosts.set(host_ids)
        add_participants(event=event, user_ids=host_ids)
    return event


@transaction.atomic
def update_event(
    *,
    event: Event,
    title: str | None = None,
    description: str | None = None,
    start_at: object | None = None,
    end_at: object | None = None,
    event_type: str | None = None,
    audiences: list[str] | None = None,
    location: object = _UNSET,
    host_ids: list[str] | None = None,
) -> Event:
    update_fields: list[str] = []
    if title is not None:
        event.title = title
        update_fields.append("title")
    if description is not None:
        event.description = description
        update_fields.append("description")
    if start_at is not None:
        event.start_at = start_at  # type: ignore[assignment]
        update_fields.append("start_at")
    if end_at is not None:
        event.end_at = end_at  # type: ignore[assignment]
        update_fields.append("end_at")
    if event_type is not None:
        event.type = event_type
        update_fields.append("type")

    if update_fields:
        update_fields.append("updated_at")
        event.save(update_fields=update_fields)

    if audiences is not None:
        EventAudience.objects.filter(event=event).delete()
        EventAudience.objects.bulk_create(
            [EventAudience(event=event, audience=a) for a in audiences]
        )

    if location is not _UNSET:
        EventLocation.objects.filter(event=event).delete()
        if location is not None:
            _build_location(event, location)  # type: ignore[arg-type]

    if host_ids is not None:
        event.hosts.set(host_ids)
        add_participants(event=event, user_ids=host_ids)

    event = reconcile_event_status(event=event)
    return event
