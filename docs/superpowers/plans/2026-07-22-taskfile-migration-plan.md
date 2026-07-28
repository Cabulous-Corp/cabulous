# Makefile → Taskfile Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 3 Makefiles (root, service, app/web) with Taskfiles, update docs, remove old Makefiles.

**Architecture:** Root `Taskfile.yml` includes `Taskfile.service.yml` and `Taskfile.app.yml` via `includes:` directive with namespaces (`service:`, `app:`). Each file mirrors the corresponding Makefile's targets 1:1. A global `setup` task handles full project bootstrap.

**Tech Stack:** go-task/task (Taskfile), YAML

## Global Constraints

- Root `Taskfile.yml` must include both child files with namespace prefixing
- `Taskfile.service.yml` lives at `service/Taskfile.service.yml`
- `Taskfile.app.yml` lives at `app/web/Taskfile.app.yml`
- All `docker compose` commands target `docker-compose.yaml` / `docker-compose.dev.yaml` (not the old `docker-compose.yml` / `.prod.yml`) — the project uses the new compose files
- Git must track: old Makefiles deleted, new Taskfile files added, docs updated
- CI unchanged (no Makefile references in workflows)
- All tasks use Taskfile `.PHONY: true` equivalent (no `@` prefix)
- No manual help task (Taskfile auto-generates via `task --list`)
- No `repo-help` target (redundant)
- `setup` from service/app moved to root `task setup`
- `setup-dev`, `up-dev`, `down-dev` etc. aliases from service removed (namespace `service:` implies dev)
- `setup` and `install` from app moved to root `task setup`

---

### Task 1: Root Taskfile.yml (dispatcher + setup)

**Files:**
- Create: `Taskfile.yml` (root)
- Delete: `Makefile` (root)

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `task setup` (global install/bootstrap), `task service:*` and `task app:*` namespaces via includes

- [ ] **Step 1: Create root Taskfile.yml with includes and setup task**

```yaml
# Taskfile.yml
# https://taskfile.dev

version: "3"

includes:
  service:
    taskfile: ./service/Taskfile.service.yml
    dir: ./service
  app:
    taskfile: ./app/web/Taskfile.app.yml
    dir: ./app/web

tasks:
  default:
    desc: "List all available tasks"
    cmd: task --list

  setup:
    desc: "Full project bootstrap (build service + install app/web)"
    cmds:
      - task: service:build
      - task: app:install
```

- [ ] **Step 2: Delete root Makefile**

- [ ] **Step 3: Commit**

```
git add Taskfile.yml Makefile
git commit -m "feat: add root Taskfile.yml with includes and setup task"
```

---

### Task 2: Service Taskfile (Docker Compose + quality + Celery)

**Files:**
- Create: `service/Taskfile.service.yml`
- Delete: `service/Makefile`

**Interfaces:**
- Consumes: nothing (standalone file)
- Produces: All `service:*` tasks consumed by root include

- [ ] **Step 1: Create service Taskfile with all 4 sections (dev, celery, prod, quality)**

```yaml
# Taskfile.service.yml
# https://taskfile.dev

version: "3"

vars:
  DEV_COMPOSE: docker compose -f docker-compose.yaml -f docker-compose.dev.yaml
  PROD_COMPOSE: docker compose -f docker-compose.yaml
  UV_RUN: uv run

tasks:
  default:
    desc: "List all service tasks"
    cmd: task --list

  # === Dev ===
  dev:
    desc: "Start dev stack with hot reload"
    cmd: '{{.DEV_COMPOSE}} up --build -d'
  up:
    desc: "Start dev stack (alias for dev)"
    cmd: '{{.DEV_COMPOSE}} up --build -d'
  down:
    desc: "Stop dev stack"
    cmd: '{{.DEV_COMPOSE}} down'
  build:
    desc: "Build dev images"
    cmd: '{{.DEV_COMPOSE}} build'
  restart:
    desc: "Restart dev stack"
    cmds:
      - task: down
      - task: up
  logs:
    desc: "Follow dev logs"
    cmd: '{{.DEV_COMPOSE}} logs -f'
  ps:
    desc: "List dev services"
    cmd: '{{.DEV_COMPOSE}} ps'
  bash:
    desc: "Open shell in web container"
    cmd: '{{.DEV_COMPOSE}} exec web sh'
  shell:
    desc: "Open Django shell"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py shell'
  dbshell:
    desc: "Open Django dbshell"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py dbshell'
  psql:
    desc: "Open psql in PostgreSQL"
    cmd: '{{.DEV_COMPOSE}} exec db sh -lc ''psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'''
  migrate:
    desc: "Apply migrations"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py migrate'
  makemigrations:
    desc: "Create migrations"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py makemigrations'
  superuser:
    desc: "Create superuser"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py createsuperuser'
  test:
    desc: "Run Django tests"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py test'
  collectstatic:
    desc: "Collect static files"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py collectstatic --noinput'
  manage:
    desc: "Run arbitrary manage.py command (usage: task service:manage CMD='check')"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py {{.CMD}}'
    vars:
      CMD: '{{.CMD}}'

  # === Celery ===
  worker:
    desc: "Start Celery worker"
    cmd: '{{.DEV_COMPOSE}} up -d --build --force-recreate worker'
  beat:
    desc: "Start Celery beat"
    cmd: '{{.DEV_COMPOSE}} up -d --build --force-recreate beat'
  flower:
    desc: "Start Flower monitoring"
    cmd: '{{.DEV_COMPOSE}} up -d --build --force-recreate flower'
  worker-logs:
    desc: "Follow worker logs"
    cmd: '{{.DEV_COMPOSE}} logs -f worker'
  beat-logs:
    desc: "Follow beat logs"
    cmd: '{{.DEV_COMPOSE}} logs -f beat'
  flower-logs:
    desc: "Follow flower logs"
    cmd: '{{.DEV_COMPOSE}} logs -f flower'
  restart-worker:
    desc: "Restart worker"
    cmd: '{{.DEV_COMPOSE}} up -d --build --force-recreate worker'
  restart-beat:
    desc: "Restart beat"
    cmd: '{{.DEV_COMPOSE}} up -d --build --force-recreate beat'
  restart-flower:
    desc: "Restart flower"
    cmd: '{{.DEV_COMPOSE}} up -d --build --force-recreate flower'

  # === Production ===
  prod:
    desc: "Start production stack"
    cmd: '{{.PROD_COMPOSE}} up --build -d'
  prod-down:
    desc: "Stop production stack"
    cmd: '{{.PROD_COMPOSE}} down'
  prod-build:
    desc: "Build production images"
    cmd: '{{.PROD_COMPOSE}} build'
  prod-restart:
    desc: "Restart production stack"
    cmds:
      - task: prod-down
      - task: prod
  prod-logs:
    desc: "Follow production logs"
    cmd: '{{.PROD_COMPOSE}} logs -f web'
  prod-ps:
    desc: "List production services"
    cmd: '{{.PROD_COMPOSE}} ps'
  prod-bash:
    desc: "Open shell in production web container"
    cmd: '{{.PROD_COMPOSE}} exec web sh'
  prod-shell:
    desc: "Open Django shell (production)"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py shell'
  prod-dbshell:
    desc: "Open Django dbshell (production)"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py dbshell'
  prod-psql:
    desc: "Open psql (production)"
    cmd: '{{.PROD_COMPOSE}} exec db sh -lc ''psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'''
  prod-migrate:
    desc: "Apply migrations (production)"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py migrate'
  prod-makemigrations:
    desc: "Create migrations (production)"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py makemigrations'
  prod-superuser:
    desc: "Create superuser (production)"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py createsuperuser'
  prod-test:
    desc: "Run tests (production)"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py test'
  prod-collectstatic:
    desc: "Collect static files (production)"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py collectstatic --noinput'
  prod-manage:
    desc: "Run manage.py in production (usage: task service:prod-manage CMD='check')"
    cmd: '{{.PROD_COMPOSE}} run --rm web {{.UV_RUN}} python manage.py {{.CMD}}'
    vars:
      CMD: '{{.CMD}}'
  prod-worker-logs:
    desc: "Worker logs (production)"
    cmd: '{{.PROD_COMPOSE}} logs -f worker'
  prod-beat-logs:
    desc: "Beat logs (production)"
    cmd: '{{.PROD_COMPOSE}} logs -f beat'
  prod-flower-logs:
    desc: "Flower logs (production)"
    cmd: '{{.PROD_COMPOSE}} logs -f flower'
  prod-restart-worker:
    desc: "Restart worker (production)"
    cmd: '{{.PROD_COMPOSE}} up -d --build --force-recreate worker'
  prod-restart-beat:
    desc: "Restart beat (production)"
    cmd: '{{.PROD_COMPOSE}} up -d --build --force-recreate beat'
  prod-restart-flower:
    desc: "Restart flower (production)"
    cmd: '{{.PROD_COMPOSE}} up -d --build --force-recreate flower'

  # === Quality ===
  lint:
    desc: "Run ruff check"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python -m ruff check .'
  format:
    desc: "Apply ruff fix + format"
    cmds:
      - '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python -m ruff check . --fix'
      - '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python -m ruff format .'
  typecheck:
    desc: "Run mypy type checking"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python -m mypy .'
  check:
    desc: "Run lint + format check + typecheck"
    cmds:
      - '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python -m ruff check .'
      - '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python -m ruff format --check .'
      - '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} python -m mypy .'
  test-ci:
    desc: "Run tests in CI mode"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} pytest tests/ -q --tb=short'
  coverage:
    desc: "Run tests with coverage"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} pytest --branch --cov=. --cov-report=term-missing --cov-report=json:coverage.json -q'
  function-length:
    desc: "Run flake8 function-length check"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} flake8 --select=C901,MFL000 --max-complexity=10 --max-function-length=50 --exclude=''*/migrations/*,*/tests/*,*/.venv/*,*/__pycache__/*,*/site-packages/*'' .'
  duplication:
    desc: "Run jscpd duplication check"
    cmd: '{{.DEV_COMPOSE}} run --rm web {{.UV_RUN}} jscpd --min-lines 5 --min-tokens 50 --reporters console .'
  migration-check:
    desc: "Check pending migrations (skipped locally, runs in CI)"
    cmds:
      - echo "migration-check: skipped locally (requires PostgreSQL); runs in CI"
  contract-check:
    desc: "Run OpenAPI contract check"
    cmd: bash ../scripts/quality/check-openapi.sh
  quality:
    desc: "Run all quality checks"
    deps:
      - lint
      - typecheck
      - test-ci
      - coverage
      - function-length
      - duplication
      - migration-check
      - contract-check
    cmds:
      - echo "All backend quality checks passed"
```

- [ ] **Step 2: Delete service/Makefile**

- [ ] **Step 3: Commit**

```
git add service/Taskfile.service.yml service/Makefile
git commit -m "feat: add Service Taskfile with Docker Compose, Celery, prod and quality tasks"
```

---

### Task 3: App Taskfile (Next.js/Bun frontend tasks)

**Files:**
- Create: `app/web/Taskfile.app.yml`
- Delete: `app/web/Makefile`

**Interfaces:**
- Consumes: nothing (standalone file)
- Produces: All `app:*` tasks consumed by root include

- [ ] **Step 1: Create app Taskfile**

```yaml
# Taskfile.app.yml
# https://taskfile.dev

version: "3"

tasks:
  default:
    desc: "List all app tasks"
    cmd: task --list

  dev:
    desc: "Start Next.js dev server"
    cmd: bun run dev

  build:
    desc: "Build Next.js app"
    cmd: bun run build

  lint:
    desc: "Run ESLint"
    cmd: bun run lint

  lint-fix:
    desc: "Run ESLint with auto-fix"
    cmd: bun run lint:fix

  lint-fix-unsafe:
    desc: "Run ESLint with unsafe auto-fix"
    cmd: bun run lint:fix-unsafe

  typecheck:
    desc: "Run TypeScript check"
    cmd: bun run typecheck

  test:
    desc: "Run Vitest tests"
    cmd: bun run test

  coverage:
    desc: "Run tests with coverage"
    cmd: bun run test:coverage

  quality:
    desc: "Run all quality checks (lint + typecheck + build + coverage)"
    cmds:
      - bun run quality
      - echo "All frontend quality checks passed!"

  generate-api-types:
    desc: "Generate API types from OpenAPI schema"
    cmds:
      - curl http://localhost:8000/openapi.json > openapi.json
      - bunx openapi-typescript openapi.json -o ./types/api.d.ts
      - rm openapi.json
```

- [ ] **Step 2: Delete app/web/Makefile**

- [ ] **Step 3: Commit**

```
git add app/web/Taskfile.app.yml app/web/Makefile
git commit -m "feat: add App Taskfile with Next.js/Bun tasks"
```

---

### Task 4: Update CLAUDE.md with Taskfile commands

**Files:**
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: Task 1-3 (Taskfiles created, Makefiles deleted)
- Produces: Updated docs referencing `task` instead of `make`

- [ ] **Step 1: Update CLAUDE.md — replace all `make` references with `task`**

Changes needed:
- `make quality` → `task service:quality`
- Add Taskfile installation instructions section
- Add migration note that Makefiles were replaced

- [ ] **Step 2: Commit**

```
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with Taskfile commands and installation"
```

---

### Task 5: Final verification and cleanup

**Files:**
- All files

**Interfaces:**
- Verifies all prior tasks are complete and consistent

- [ ] **Step 1: Verify no Makefiles remain in the main repo**

```
find . -maxdepth 3 -name Makefile -not -path './.worktrees/*' -not -path './.claude/*' -not -path './node_modules/*' -not -path './.uv-cache/*'
```

Expected output: nothing (no Makefiles found)

- [ ] **Step 2: Verify all three Taskfiles exist**

```
ls -la Taskfile.yml service/Taskfile.service.yml app/web/Taskfile.app.yml
```

Expected: 3 files exist

- [ ] **Step 3: Verify `task --list` works**

```
task --list
```

Expected: lists all service:* and app:* tasks plus setup

- [ ] **Step 4: Verify CLAUDE.md has no remaining `make` references**

```
grep -n "make " CLAUDE.md
```

Expected: only references to "Makefile" in historic context, not as commands

- [ ] **Step 5: Final commit with any fixes**

```
git commit -m "chore: final cleanup after Makefile→Taskfile migration"
```
