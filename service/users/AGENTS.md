# Backend module: `users`

## Purpose

Profile and identity surface. Owns the custom `User` model, magic-link authentication artifacts, profile data, media upload signing, and user-facing API behavior.

## Owned code

- Models: `service/users/models.py`
- Views/serializers: `service/users/views.py`, `service/users/serializers.py`
- Upload helpers: `service/users/services/upload_signing.py`
- URLs/tasks/admin: `service/users/urls.py`, `service/users/tasks.py`, `service/users/admin.py`

## Boundaries

- `AUTH_USER_MODEL` is `users.User`; auth-dependent behavior in other apps should treat this as the source of truth for identity.
- Actual media storage is owned by `media`; `users` defines upload keys and signed-url generation only.
- Handles onboarding state, soft-delete behavior, and cleanup of auth tokens.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Sensitive filename/state derivation helpers live in `service/users/models.py`.
- Signed upload behavior should be tested via service-level cases; avoid exposing MinIO internals across packages.
