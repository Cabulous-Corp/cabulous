# Backend module: `authentication`

## Purpose

Auth boundary. Owns login/logout/refresh flows, onboarding first-access enforcement, password-reset handling, and periodic JWT cleanup.

## Owned code

- Models: `service/authentication/models.py`
- Views: `service/authentication/views.py`
- URLs: `service/authentication/urls.py`
- Admin/tasks: `service/authentication/admin.py`, `service/authentication/tasks.py`

## Boundaries

- Owns `authentication.*` endpoints under `/api/auth/`.
- Depends on `users.User` as the auth identity model; do not duplicate user state here.
- Reuses `communication` for email delivery and `monitoring` for health behavior when needed.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Auth behavior flows through tasks/configurable Celery beat jobs declared in `service/cabulous/settings.py`.
- Changes to auth requirements should land as model or serializer-level rules, plus tests under `service/authentication/tests/`.
