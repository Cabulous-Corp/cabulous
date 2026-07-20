# Backend module: `monitoring`

## Purpose

System health surface. Owns lightweight health/status endpoints and simple Celery-driven liveness behavior.

## Owned code

- Health view: `service/monitoring/views.py`
- URLs/admin/tasks: `service/monitoring/urls.py`, `service/monitoring/admin.py`, `service/monitoring/tasks.py`

## Boundaries

- Should stay intentionally cheap; avoid adding business state or blocking dependencies to health checks.
- Models are currently placeholder-only; if a model is added, it should belong in a more specific app unless it is truly cross-cutting infra.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Health checks are part of deployment reliability; keep contract changes explicit and minimal.
