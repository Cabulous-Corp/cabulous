# Backend module: `analytics`

## Purpose

Party statistics and derived analytics state. Owns aggregate domain models and admin exploration for analytics data.

## Owned code

- Models: `service/analytics/models.py`
- Admin: `service/analytics/admin.py`

## Boundaries

- Currently limited to aggregate statistics linked to `users.User`.
- Does not own raw user behavior sources; those belong in `events` or other domain apps.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Derived fields in `PartyStatistics.save()` are preserved; avoid splitting them into separate compute flows without a migration plan.
