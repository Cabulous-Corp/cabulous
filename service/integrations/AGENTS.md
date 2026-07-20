# Backend module: `integrations`

## Purpose

External integration surface. Owns webhook entrypoints and inbound external data flows.

## Owned code

- Views/admin/urls: `service/integrations/views.py`, `service/integrations/admin.py`, `service/integrations/urls.py`

## Boundaries

- Currently represented by placeholder GitHub webhook handling; expand carefully around webhook resilience and idempotency.
- Should hand off domain-specific processing instead of embedding business rules deeply.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Webhook endpoints are externally reachable; keep security validation explicit and close to the view layer.
