import re
from typing import Any

import phonenumbers
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from phonenumbers import NumberParseException
from phonenumbers.phonenumberutil import PhoneNumberFormat

USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]+$")
DISCORD_USERNAME_PATTERN = re.compile(r"^[a-z0-9._]+$")
DEFAULT_PHONE_REGION = "BR"


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


def normalize_discord_username(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.startswith("@"):
        normalized = normalized[1:]
    return normalized


def validate_discord_username_format(value: str) -> None:
    if not value:
        return
    if " " in value:
        raise ValidationError("Discord username cannot contain spaces.")
    if not DISCORD_USERNAME_PATTERN.fullmatch(value):
        raise ValidationError(
            "Discord username can only contain lowercase letters, numbers, dots, and underscores."
        )


def clean_discord_username(value: str) -> str:
    normalized = normalize_discord_username(value)
    validate_discord_username_format(normalized)
    return normalized


def normalize_phone_number(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    try:
        parsed = phonenumbers.parse(normalized, DEFAULT_PHONE_REGION)
    except NumberParseException:
        return normalized
    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)


def validate_phone_number_format(value: str) -> None:
    if not value:
        return
    try:
        parsed = phonenumbers.parse(value, DEFAULT_PHONE_REGION)
    except NumberParseException as exc:
        raise ValidationError("Invalid phone number.") from exc
    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError("Invalid phone number.")


def clean_phone_number(value: str) -> str:
    normalized = normalize_phone_number(value)
    validate_phone_number_format(normalized)
    return normalized
