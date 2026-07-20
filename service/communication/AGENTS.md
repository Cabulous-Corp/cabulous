# Backend module: `communication`

## Purpose

Outbound messaging boundary. Owns email delivery and Discord webhook/messaging behavior.

## Owned code

- Models/helpers: `service/communication/models/`, `service/communication/helpers/`
- Service layer: `service/communication/services/`
- Tasks/URLs/admin: `service/communication/tasks.py`, `service/communication/urls.py`, `service/communication/admin.py`

## Boundaries

- Should remain a thin transport layer; business rules about when/why to notify belong in the domain app.
- Keeps message template/payload contracts; do not leak raw webhook secrets into model state unnecessarily.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Prefer Celery tasks for outbound side effects; keep view-level code readable and non-blocking.
- Template rendering and payload validation already live under `service/communication/services/`.
