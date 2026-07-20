# Backend module: `media`

## Purpose

Global media registry. Owns shared photo metadata and storage identity for later association with domain objects.

## Owned code

- Models: `service/media/models.py`
- Tests: `service/media/tests/test_models.py`

## Boundaries

- Represents uploaded object metadata only; actual file/blob lifecycle interacts with `common.storage_backends` and MinIO/S3 settings.
- Other apps should associate with `media.Photo`; avoid duplicating object/size/content-type metadata elsewhere.

## Validation commands

- `make service manage cmd='check'`
- `make service test`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Media metadata changes should preserve deterministic ordering/indexing for `taken_on` and `created_at` lookups where possible.
