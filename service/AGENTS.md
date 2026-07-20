# Backend service guidance

These rules apply to every package under `service/`. Individual app docs (`service/*/AGENTS.md`) inherit from this file and should only add app-specific boundaries or commands.

## Django app structure

- Every first-party package under `service/` is a Django app; its `apps.py` declares the app name.
- Keep domain logic close to `models.py`; use `services/` only for external/connector behavior; keep `tasks.py` minimal wrappers.
- Identifiers and user-facing strings in this project are already in Portuguese; preserve existing vocabulary when changing behavior.
- `service/common` is shared infrastructure (`BaseModel`, soft delete, storage backends). Avoid creating another shared app without a shared reason.

## Local commands

- Backend targets are routed through the repo root: `make service <target>`, `make service manage cmd='<command>'`.
- Examples:
  - `make service makemigrations`
  - `make service makemigrations-dev`
  - `make service manage cmd='makemigrations analytics users'`
  - `make service test`
  - `make service manage cmd='check'`

## Migration policy

Migrations are part of the codebase and require the same review rigor as models or tests.

- Models are the source of truth for structural schema.
- Normally generate structural migrations with `make makemigrations` or `make service manage cmd='makemigrations <app> ...'` when selecting specific apps or flags.
- If migrations and models diverge, fix the mismatch in code; don't hand-write structural operations to hide drift.
- Commit generated migrations with the matching model change; the developer and reviewer must be able to explain every operation in the new migration file.
- Require `make service manage cmd='makemigrations --check --dry-run --noinput'` to report `No changes detected` before merging a model change.
- Hand-edit or add migration code only for explicit exceptional operations such as data preservation (`RunPython`/reverse) or a proven operation-order requirement.
- Never rewrite deployed migrations. If a deployed migration needs correction, add a new incremental migration that safely moves the schema forward.
