# Agent Instructions

## Repo layout

Monorepo with two distinct apps, each with its own toolchain. Always `cd` into the
right directory before running commands:

- `service/` — Django + DRF backend (Python 3.13, `uv`, Postgres 17, Redis, Celery,
  Flower, MinIO). Entrypoint: `service/manage.py`. Settings module: `cabulous.settings`.
- `app/web/` — Next.js 16 frontend (Bun, React 19, Tailwind v4, Vitest). Has its own
  `AGENTS.md` with frontend-specific conventions.

Run dev stacks via `task` (root `Taskfile.yml` includes both):
`task service:dev`, `task service:up`, `task app:dev`, `task app:quality`.

## Backend: high-signal gotchas

- **Run backend commands from `service/`.** Many scripts assume `cwd=service`.
  The Taskfile `service:*` tasks handle this automatically via the `dir:` directive;
  raw invocations (e.g. `uv run pytest`) do not.
- **Settings come from pydantic-settings** (`service/cabulous/config.py`), not plain
  Django settings. Env vars use `__` nesting (`DATABASE__HOST`, `REDIS__URL`,
  `CELERY__BROKER_URL`, `MINIO__ACCESS_KEY`, `JWT__...`, `EMAIL__...`). Defaults in
  `config.py` are functional for local dev, so most commands run without a `.env`.
- **Tests are split per Django app**, declared in `service/pytest.ini` `testpaths`:
  `tests events/tests media/tests comments/tests users/tests authentication/tests
  communication/tests monitoring/tests`. There is no top-level `conftest.py`; tests
  rely on `pytest-django` + `DJANGO_SETTINGS_MODULE=cabulous.settings` from `pytest.ini`.
- **Run a single test file or test:** `uv run pytest events/tests/test_something.py::TestClass::test_method -q`.
- **Backend tests needing DB/Redis:** `pytest.ini` does not bootstrap services. The
  `backend-test` CI job provisions Postgres 16 + Redis 7 services and sets
  `DATABASE__HOST=localhost`, `REDIS__URL=redis://localhost:6379/1`, `SECRET_KEY`.
  Replicate those env vars locally if you run `pytest` outside Docker.
- **Coverage gate:** `pyproject.toml` `[tool.coverage.report] fail_under = 25`.
  Migrations, `*/tests/*`, and `conftest.py` are omitted from coverage. Don't write
  tests that only cover migrations to game coverage.
- **Migrations:** never edit generated migrations. `backend-migration` CI runs
  `manage.py makemigrations --check --dry-run` against Postgres; missing migrations
  fail CI. Local `task service:migration-check` is intentionally a no-op (no Postgres
  locally) — don't trust it as a green signal.
- **mypy config:** `disallow_untyped_defs = true`, mypy plugin
  `mypy_django_plugin.main` with `django_settings_module = cabulous.settings`.
  Migrations for `events` and `comments` are ignored (`ignore_errors = true`); do
  not type-check those. Celery and `django_filters` imports are ignored.
- **Ruff:** line-length 100, rule set `E,F,I,UP,B,SIM,C4`. `*/migrations/*.py` and
  `*/fixtures/*` are excluded from lint — keep fixtures in those paths.
- **Function length gate:** flake8 `max-function-length=50`, `max-complexity=10`.
  Applies to non-test, non-migration, non-venv code. Long test functions are excluded.
- **OpenAPI contract:** `quality/openapi/baseline.json` is the committed contract.
  `scripts/quality/check-openapi.sh` (run by `task service:contract-check` /
  `backend-contract` CI) fails on breaking changes unless a waiver exists in
  `quality/exceptions/openapi-waivers.yaml`. Add a waiver with `expires` + justification
  for intentional breaking changes.
- **Duplication ratchet:** `quality/baselines/jscpd.json` pins current duplicate totals.
  New duplicates or growth fails `backend-duplication` CI. To accept new known
  duplicates, update the baseline JSON and commit it with the code change.

## Frontend: high-signal gotchas

- Use **Bun**, not npm/yarn. Lockfile is `app/web/bun.lock`.
- Quality gate order (matches `package.json` `quality` script):
  `lint -> typecheck -> build -> test:coverage`.
- API types are generated from the backend OpenAPI schema:
  `task app:generate-api-types` (requires backend running on `localhost:8000`).
  Don't hand-edit `types/api.d.ts`.
- See `app/web/AGENTS.md` for frontend conventions.

## CI suite (run before marking a task complete)

The CI workflow (`.github/workflows/quality.yml`) gates both apps. Run locally:

```bash
# Backend — from service/
cd service
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest --tb=short --cov=. --cov-report=term-missing -q
```

```bash
# Frontend — from app/web/
cd app/web
bun run lint
bun run typecheck
bun run build
bun run test:coverage
```

Blocking CI jobs you must keep green: `backend-lint`, `backend-typecheck`,
`backend-test`, `backend-duplication`, `backend-contract`, `backend-migration`,
`frontend-lint`, `frontend-typecheck`, `frontend-build`, `frontend-test`.
`semgrep` and `gitleaks` are observational (`continue-on-error`); fix findings anyway.

Fix any failures before marking the task complete. Every commit on a branch must
keep CI green.