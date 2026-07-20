# Backend module: `cabulous`

## Purpose

Top-level Django project package. Owns settings, URL routing, ASGI/WSGI entrypoints, Celery app wiring, and environment configuration for every backend service.

## Owned code

- Configuration: `service/cabulous/config.py`
- Settings: `service/cabulous/settings.py`
- App/process entrypoints: `service/cabulous/asgi.py`, `service/cabulous/wsgi.py`, `service/cabulous/celery.py`
- Root backend URL map: `service/cabulous/urls.py`

## Boundaries

- Does not define business-domain models or per-feature views.
- First-party domain logic lives under `service/<app>/`; shared abstractions live in `service/common`.
- Frontend code stays under `app/web/`.

## Validation commands

- `make service manage cmd='check'`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- First-party apps are registered in `INSTALLED_APPS` inside `service/cabulous/settings.py`; add new apps there.
- External integrations and secrets flow through `service/cabulous/config.py`; do not hardcode values in app code.
- See `service/AGENTS.md` for shared backend workflow, especially the migration policy.
