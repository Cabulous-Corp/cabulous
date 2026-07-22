from __future__ import annotations

from django.db import transaction
from rest_framework.exceptions import ValidationError

from events.models import EventPhoto, Highlight, HighlightPhoto
from users.models import User


@transaction.atomic
def create_highlight(
    *,
    event,
    author: User,
    text: str,
    photo_ids: list[str] | None = None,
) -> Highlight:
    """Create a highlight with optional linked photos."""
    photo_ids = photo_ids or []

    if photo_ids:
        linked = set(
            EventPhoto.objects.filter(event=event, photo_id__in=photo_ids).values_list(
                "photo_id", flat=True
            )
        )
        missing = set(photo_ids) - linked
        if missing:
            joined = ", ".join(str(p) for p in missing)
            raise ValidationError({"photo_ids": f"Photos not linked to this event: {joined}"})

    hl = Highlight.objects.create(event=event, author=author, text=text)
    if photo_ids:
        HighlightPhoto.objects.bulk_create(
            [HighlightPhoto(highlight=hl, photo_id=pid) for pid in photo_ids]
        )
    return hl


@transaction.atomic
def update_highlight(
    *,
    highlight: Highlight,
    text: str | None = None,
    photo_ids: list[str] | None = None,
) -> Highlight:
    """Update a highlight's text and/or replace its photos."""
    if text is not None:
        highlight.text = text
        highlight.save(update_fields=["text", "updated_at"])

    if photo_ids is not None:
        linked = set(
            EventPhoto.objects.filter(event=highlight.event, photo_id__in=photo_ids).values_list(
                "photo_id", flat=True
            )
        )
        missing = set(photo_ids) - linked
        if missing:
            joined = ", ".join(str(p) for p in missing)
            raise ValidationError({"photo_ids": f"Photos not linked to this event: {joined}"})
        highlight.photos.all().delete()
        if photo_ids:
            HighlightPhoto.objects.bulk_create(
                [HighlightPhoto(highlight=highlight, photo_id=pid) for pid in photo_ids]
            )

    return highlight


def delete_highlight(*, highlight: Highlight) -> None:
    """Delete a highlight. Only removes join table records — Photo objects are never deleted."""
    highlight.delete()
