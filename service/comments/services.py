from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Comment
from .targets import resolve_target_model


def _validate_target_id(target_type: str, target_id: Any) -> Any:
    model_cls = resolve_target_model(target_type)
    try:
        instance = model_cls.objects.get(pk=target_id)  # type: ignore[attr-defined]
    except model_cls.DoesNotExist:  # type: ignore[attr-defined]
        raise ValidationError({"target_id": "Target object does not exist."}) from None
    # For soft-deletable models, reject deleted targets
    if getattr(instance, "deleted_at", None) is not None:
        raise ValidationError({"target_id": "Target object is deleted."})
    return instance


@transaction.atomic()
def create_comment(
    *,
    author: Any,
    target_type: str,
    target_id: Any,
    body: str,
    parent: Comment | None = None,
) -> Comment:
    target = _validate_target_id(target_type, target_id)

    content_type = ContentType.objects.get_for_model(target)
    object_id = target.id

    if parent is not None and (
        parent.content_type_id != content_type.id or parent.object_id != object_id
    ):
        raise ValidationError({"parent": "Child comment must share the same target as its parent."})

    comment = Comment(
        author=author,
        body=body,
        parent=parent,
        content_type=content_type,
        object_id=object_id,
    )
    comment.full_clean()
    comment.save()
    return comment


def soft_delete_comment(*, comment: Comment) -> None:
    comment.body = ""
    comment.deleted_at = timezone.now()
    comment.save(update_fields=["body", "deleted_at", "updated_at"])
