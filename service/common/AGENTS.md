# Backend module: `common`

## Purpose

Shared Django foundation for every service app.

## Owned code

- Base abstractions: `service/common/models/abstracts.py`
- Shared storage/model helpers as present in `service/common/`

## Boundaries

- Provides cross-cutting base classes such as base models and soft-delete behavior.
- Should not contain business-specific models, views, or task flows.
- Other apps depend on `common`; changes here can affect migrations or behavior everywhere.

## Validation commands

- `make service manage cmd='check'`
- `make service manage cmd='makemigrations --check --dry-run --noinput'`

## Local conventions

- Treat `common` as stable infrastructure: prefer addition of abstract helpers over changing existing abstract class names or behavior.
- Model or migration changes here should be reviewed across all dependent apps.
