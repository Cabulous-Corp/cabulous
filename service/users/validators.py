import re
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import QuerySet

USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]+$")


def normalize_username(value: str) -> str:
    return value.strip().lower()


def validate_username_format(value: str) -> None:
    if not value:
        raise ValidationError("Username is required.")
    if " " in value:
        raise ValidationError("Username cannot contain spaces.")
    if not USERNAME_PATTERN.fullmatch(value):
        raise ValidationError(
            "Username can only contain lowercase letters, numbers, dots, underscores, and hyphens."
        )


def ensure_username_available(
    queryset: QuerySet,
    username: str,
    *,
    exclude_pk: Any = None,
) -> None:
    candidates = queryset.filter(username__iexact=username)
    if exclude_pk is not None:
        candidates = candidates.exclude(pk=exclude_pk)
    if candidates.exists():
        raise ValidationError("This username is already in use.")


def clean_username(
    value: str,
    *,
    queryset: QuerySet | None = None,
    exclude_pk: Any = None,
) -> str:
    normalized = normalize_username(value)
    validate_username_format(normalized)
    if queryset is not None:
        ensure_username_available(queryset, normalized, exclude_pk=exclude_pk)
    return normalized
