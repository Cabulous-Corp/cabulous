from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from events.models import Event, EventParticipant, EventPhoto
from media.models import Photo
from users.models import User


def add_participants(*, event: Event, user_ids: list[str]) -> list[EventParticipant]:
    """Batch-add participants. Skips inactive/deleted/nonexistent users, idempotent on duplicates."""
    users = User.objects.filter(id__in=user_ids, is_active=True, deleted_at__isnull=True)
    found_ids = {str(u.id) for u in users}

    invalid = [uid for uid in user_ids if uid not in found_ids]
    if invalid:
        raise ValidationError({"user_ids": f"Invalid or inactive user IDs: {', '.join(invalid)}"})

    rows = [EventParticipant(event=event, user_id=uid) for uid in user_ids]
    return EventParticipant.objects.bulk_create(rows, ignore_conflicts=True)


def remove_participant(*, event: Event, user_id: str) -> None:
    """Remove a participant. Prevents removing the event creator."""
    if str(event.creator_id) == user_id:
        raise ValidationError({"detail": "Cannot remove the event creator."})
    deleted, _ = EventParticipant.objects.filter(event=event, user_id=user_id).delete()
    if deleted == 0:
        raise NotFound({"detail": "Participant not found."})


def link_photo(*, event: Event, photo: Photo, user: User) -> EventPhoto:
    """Link a photo to an event. Idempotent if already linked."""
    obj, _ = EventPhoto.objects.get_or_create(
        event=event, photo=photo, defaults={"linked_by": user}
    )
    return obj


def unlink_photo(*, event: Event, photo_id: str) -> None:
    """Unlink a photo from an event."""
    deleted, _ = EventPhoto.objects.filter(event=event, photo_id=photo_id).delete()
    if deleted == 0:
        raise NotFound({"detail": "Photo not linked to this event."})


def can_unlink(*, event: Event, photo_id: str, user: User) -> bool:
    """Check if user can unlink a photo: creator/staff always, otherwise only their own link."""
    if user.is_staff or event.creator_id == user.id:
        return True
    return EventPhoto.objects.filter(
        event=event, photo_id=photo_id, linked_by=user
    ).exists()


@transaction.atomic
def set_thumbnail(*, event: Event, photo: Photo | None) -> EventPhoto | None:
    """Set the thumbnail for an event. Pass None to clear."""
    EventPhoto.objects.filter(event=event, is_thumbnail=True).update(is_thumbnail=False)
    if photo is None:
        return None
    relation = EventPhoto.objects.filter(event=event, photo=photo).first()
    if relation is None:
        raise ValidationError({"photo_id": "Photo is not linked to this event."})
    # ponytail: IntegrityError from concurrent thumbnail set — catch and re-read
    try:
        relation.is_thumbnail = True
        relation.save(update_fields=["is_thumbnail", "updated_at"])
    except IntegrityError:
        relation.refresh_from_db()
    return relation
