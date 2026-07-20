# Backend module: `events`

## Purpose

Event domain. Owns events, audiences, participants, locations, event photos, and related enum/color metadata.

## Owned code

- Domain modules: `service/events/enums.py`, `service/events/constants.py`, `service/events/models.py`
- Web/admin/tests: `service/events/views.py`, `service/events/admin.py`, `service/events/tests/`

## Boundaries

- References `users.User` for creators/participants and `media.Photo` for event photos.
- Soft delete is enforced through custom managers in `Event`; use explicit managers instead of raw querysets.
- Historical migrations exist under `service/events/migrations/`; do not rewrite them.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Status-related fields (`end_at`, `status`, `cancelled_at`) are derived/validated in model methods/clean; keep business meaning inside the models layer.
- See `service/AGENTS.md` for migration policy: prefer new incremental migrations after deployment.
