from __future__ import annotations

from django.db import transaction
from rest_framework.exceptions import ValidationError

from events.models import Highlight, HighlightPhoto
from media.models import Photo
from users.models import User


@transaction.atomic
def create_highlight(
    *,
    event,
    author: User,
    text: str,
    photo_ids: list[str] | None = None,
) -> Highlight:
    """Create a highlight with optional linked photos. Validates all photo_ids exist before creating anything."""
    photo_ids = photo_ids or []

    if photo_ids:
        existing = set(
            Photo.objects.filter(id__in=photo_ids).values_list("id", flat=True)
        )
        missing = set(photo_ids) - existing
        if missing:
            raise ValidationError(
                {"photo_ids": f"Invalid photo IDs: {', '.join(str(p) for p in missing)}"}
            )

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
    """Update a highlight's text and/or replace its photos. Validates photo_ids before touching anything."""
    if text is not None:
        highlight.text = text
        highlight.save(update_fields=["text", "updated_at"])

    if photo_ids is not None:
        existing = set(
            Photo.objects.filter(id__in=photo_ids).values_list("id", flat=True)
        )
        missing = set(photo_ids) - existing
        if missing:
            raise ValidationError(
                {"photo_ids": f"Invalid photo IDs: {', '.join(str(p) for p in missing)}"}
            )
        highlight.photos.all().delete()
        if photo_ids:
            HighlightPhoto.objects.bulk_create(
                [HighlightPhoto(highlight=highlight, photo_id=pid) for pid in photo_ids]
            )

    return highlight


@transaction.atomic
def delete_highlight(*, highlight: Highlight) -> None:
    """Delete a highlight. Only removes join table records — Photo objects are never deleted."""
    highlight.delete()
