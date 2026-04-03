PROD_COMPOSE = docker compose -f docker-compose.yaml
DEV_COMPOSE = docker compose -f docker-compose.yaml -f docker-compose.dev.yaml
CONTAINER_UV_RUN = uv run

cmd ?=
MANAGE_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
MANAGE_CMD ?= $(cmd)

ALL_TARGETS := help setup setup-dev up down build restart logs ps bash shell dbshell psql migrate makemigrations superuser test collectstatic manage web-logs db-logs redis-logs minio-logs minio-init-logs worker-logs beat-logs flower-logs restart-worker restart-beat restart-flower up-dev down-dev build-dev restart-dev logs-dev ps-dev bash-dev shell-dev dbshell-dev psql-dev migrate-dev makemigrations-dev superuser-dev test-dev collectstatic-dev manage-dev web-logs-dev db-logs-dev redis-logs-dev minio-logs-dev minio-init-logs-dev worker-logs-dev beat-logs-dev flower-logs-dev restart-worker-dev restart-beat-dev restart-flower-dev up-prod down-prod build-prod restart-prod logs-prod ps-prod bash-prod shell-prod dbshell-prod psql-prod migrate-prod makemigrations-prod superuser-prod test-prod collectstatic-prod manage-prod web-logs-prod db-logs-prod redis-logs-prod minio-logs-prod minio-init-logs-prod worker-logs-prod beat-logs-prod flower-logs-prod restart-worker-prod restart-beat-prod restart-flower-prod lint format typecheck check

ifneq ($(filter manage manage-dev manage-prod,$(firstword $(MAKECMDGOALS))),)
  ifeq ($(strip $(MANAGE_CMD)),)
    MANAGE_CMD := $(strip $(MANAGE_ARGS))
  endif
  MANAGE_EXTRA_NON_TARGETS := $(filter-out $(ALL_TARGETS),$(MANAGE_ARGS))
  ifneq ($(MANAGE_EXTRA_NON_TARGETS),)
    $(foreach arg,$(MANAGE_EXTRA_NON_TARGETS),$(eval $(arg):;@:))
  endif
endif

.PHONY: help
.PHONY: up down build restart logs ps bash shell dbshell psql migrate makemigrations superuser test collectstatic manage
.PHONY: web-logs db-logs redis-logs minio-logs minio-init-logs worker-logs beat-logs flower-logs
.PHONY: restart-worker restart-beat restart-flower
.PHONY: up-dev down-dev restart-dev logs-dev ps-dev bash-dev shell-dev dbshell-dev psql-dev migrate-dev makemigrations-dev superuser-dev test-dev manage-dev
.PHONY: web-logs-dev db-logs-dev redis-logs-dev minio-logs-dev minio-init-logs-dev worker-logs-dev beat-logs-dev flower-logs-dev
.PHONY: restart-worker-dev restart-beat-dev restart-flower-dev
.PHONY: up-prod down-prod build-prod restart-prod logs-prod ps-prod bash-prod shell-prod dbshell-prod psql-prod migrate-prod makemigrations-prod superuser-prod test-prod collectstatic-prod manage-prod
.PHONY: web-logs-prod db-logs-prod redis-logs-prod minio-logs-prod minio-init-logs-prod worker-logs-prod beat-logs-prod flower-logs-prod
.PHONY: restart-worker-prod restart-beat-prod restart-flower-prod
.PHONY: setup setup-dev lint format typecheck check

help:
	@echo "Uso: make <target>"
	@echo ""
	@echo "# Desenvolvimento (Padrao)"
	@echo "  make setup                 - setup completo (.env, dependencias e hooks git)"
	@echo "  make up                    - sobe a stack dev com hot reload"
	@echo "  make down                  - derruba a stack dev"
	@echo "  make build                 - rebuilda as imagens da stack dev"
	@echo "  make restart               - reinicia a stack dev"
	@echo "  make logs                  - acompanha logs da stack dev"
	@echo "  make ps                    - lista servicos da stack dev"
	@echo "  make bash                  - abre shell no container web (dev)"
	@echo "  make shell                 - abre Django shell (dev)"
	@echo "  make dbshell               - abre dbshell do Django (dev)"
	@echo "  make psql                  - abre psql no Postgres (dev)"
	@echo "  make migrate               - aplica migracoes (dev)"
	@echo "  make makemigrations        - cria migracoes (dev)"
	@echo "  make superuser             - cria superusuario (dev)"
	@echo "  make test                  - roda testes (dev)"
	@echo "  make collectstatic         - coleta arquivos estaticos (dev)"
	@echo "  make manage cmd='check'    - comando arbitrario do manage.py (dev)"
	@echo ""
	@echo "# Desenvolvimento Celery (Padrao)"
	@echo "  make web-logs              - logs do web (dev)"
	@echo "  make db-logs               - logs do db (dev)"
	@echo "  make redis-logs            - logs do redis (dev)"
	@echo "  make minio-logs            - logs do minio (dev)"
	@echo "  make minio-init-logs       - logs do minio-init (dev)"
	@echo "  make worker-logs           - logs do worker (dev)"
	@echo "  make beat-logs             - logs do beat (dev)"
	@echo "  make flower-logs           - logs do flower (dev)"
	@echo "  make restart-worker        - recria worker (dev)"
	@echo "  make restart-beat          - recria beat (dev)"
	@echo "  make restart-flower        - recria flower (dev)"
	@echo ""
	@echo "# Producao"
	@echo "  make up-prod               - sobe a stack de producao"
	@echo "  make down-prod             - derruba a stack de producao"
	@echo "  make build-prod            - rebuilda imagens de producao"
	@echo "  make restart-prod          - reinicia a stack de producao"
	@echo "  make logs-prod             - logs do web em producao"
	@echo "  make ps-prod               - lista servicos de producao"
	@echo "  make bash-prod             - shell no web de producao"
	@echo "  make shell-prod            - Django shell em producao"
	@echo "  make dbshell-prod          - dbshell em producao"
	@echo "  make psql-prod             - psql em producao"
	@echo "  make migrate-prod          - aplica migracoes em producao"
	@echo "  make makemigrations-prod   - cria migracoes em producao"
	@echo "  make superuser-prod        - cria superusuario em producao"
	@echo "  make test-prod             - roda testes em producao"
	@echo "  make collectstatic-prod    - coleta estaticos em producao"
	@echo "  make manage-prod cmd='check' - comando manage.py em producao"
	@echo ""
	@echo "# Qualidade"
	@echo "  make lint                  - roda o ruff"
	@echo "  make format                - aplica autofix + formatacao com ruff"
	@echo "  make typecheck             - roda mypy (django-stubs)"
	@echo "  make check                 - roda lint + format check + mypy"

# Dev-first (targets principais)
setup:
	uv run python -c "from pathlib import Path; import shutil; env=Path('.env'); ex=Path('.env.example'); exists=env.exists(); print('.env ja existe; mantendo arquivo atual' if exists else '.env criado a partir de .env.example'); shutil.copyfile(ex, env) if not exists else None"
	uv sync --all-groups
	uv run pre-commit install --config ../.pre-commit-config.yaml --hook-type pre-commit --hook-type pre-push

up:
	$(DEV_COMPOSE) up --build -d

down:
	$(DEV_COMPOSE) down

build:
	$(DEV_COMPOSE) build

restart: down up

logs:
	$(DEV_COMPOSE) logs -f

web-logs:
	$(DEV_COMPOSE) logs -f web

db-logs:
	$(DEV_COMPOSE) logs -f db

redis-logs:
	$(DEV_COMPOSE) logs -f redis

minio-logs:
	$(DEV_COMPOSE) logs -f minio

minio-init-logs:
	$(DEV_COMPOSE) logs -f minio-init

ps:
	$(DEV_COMPOSE) ps

bash:
	$(DEV_COMPOSE) exec web sh

shell:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py shell

dbshell:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py dbshell

psql:
	$(DEV_COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

migrate:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py migrate

makemigrations:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py makemigrations

superuser:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py createsuperuser

test:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py test

collectstatic:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py collectstatic --noinput

manage:
	$(if $(strip $(filter $(ALL_TARGETS),$(MANAGE_ARGS))),@:, $(if $(strip $(MANAGE_CMD)),,@echo "Uso: make manage <comando> ou make manage cmd='<comando>'" && exit 1))
	$(if $(strip $(filter $(ALL_TARGETS),$(MANAGE_ARGS))),@:, $(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py $(MANAGE_CMD))

worker-logs:
	$(DEV_COMPOSE) logs -f worker

beat-logs:
	$(DEV_COMPOSE) logs -f beat

flower-logs:
	$(DEV_COMPOSE) logs -f flower

restart-worker:
	$(DEV_COMPOSE) up -d --build --force-recreate worker

restart-beat:
	$(DEV_COMPOSE) up -d --build --force-recreate beat

restart-flower:
	$(DEV_COMPOSE) up -d --build --force-recreate flower

# Aliases dev (compatibilidade)
setup-dev: setup
up-dev: up
down-dev: down
build-dev: build
restart-dev: restart
logs-dev: logs
ps-dev: ps
bash-dev: bash
shell-dev: shell
dbshell-dev: dbshell
psql-dev: psql
migrate-dev: migrate
makemigrations-dev: makemigrations
superuser-dev: superuser
test-dev: test
collectstatic-dev: collectstatic
manage-dev: manage
web-logs-dev: web-logs
db-logs-dev: db-logs
redis-logs-dev: redis-logs
minio-logs-dev: minio-logs
minio-init-logs-dev: minio-init-logs
worker-logs-dev: worker-logs
beat-logs-dev: beat-logs
flower-logs-dev: flower-logs
restart-worker-dev: restart-worker
restart-beat-dev: restart-beat
restart-flower-dev: restart-flower

# Producao (explicito)
up-prod:
	$(PROD_COMPOSE) up --build -d

down-prod:
	$(PROD_COMPOSE) down

build-prod:
	$(PROD_COMPOSE) build

restart-prod: down-prod up-prod

logs-prod:
	$(PROD_COMPOSE) logs -f web

web-logs-prod:
	$(PROD_COMPOSE) logs -f web

db-logs-prod:
	$(PROD_COMPOSE) logs -f db

redis-logs-prod:
	$(PROD_COMPOSE) logs -f redis

minio-logs-prod:
	$(PROD_COMPOSE) logs -f minio

minio-init-logs-prod:
	$(PROD_COMPOSE) logs -f minio-init

ps-prod:
	$(PROD_COMPOSE) ps

bash-prod:
	$(PROD_COMPOSE) exec web sh

shell-prod:
	$(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py shell

dbshell-prod:
	$(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py dbshell

psql-prod:
	$(PROD_COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

migrate-prod:
	$(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py migrate

makemigrations-prod:
	$(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py makemigrations

superuser-prod:
	$(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py createsuperuser

test-prod:
	$(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py test

collectstatic-prod:
	$(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py collectstatic --noinput

manage-prod:
	$(if $(strip $(filter $(ALL_TARGETS),$(MANAGE_ARGS))),@:, $(if $(strip $(MANAGE_CMD)),,@echo "Uso: make manage-prod <comando> ou make manage-prod cmd='<comando>'" && exit 1))
	$(if $(strip $(filter $(ALL_TARGETS),$(MANAGE_ARGS))),@:, $(PROD_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python manage.py $(MANAGE_CMD))

worker-logs-prod:
	$(PROD_COMPOSE) logs -f worker

beat-logs-prod:
	$(PROD_COMPOSE) logs -f beat

flower-logs-prod:
	$(PROD_COMPOSE) logs -f flower

restart-worker-prod:
	$(PROD_COMPOSE) up -d --build --force-recreate worker

restart-beat-prod:
	$(PROD_COMPOSE) up -d --build --force-recreate beat

restart-flower-prod:
	$(PROD_COMPOSE) up -d --build --force-recreate flower

# Qualidade
lint:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python -m ruff check .

format:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python -m ruff check . --fix
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python -m ruff format .

typecheck:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python -m mypy .

check:
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python -m ruff check .
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python -m ruff format --check .
	$(DEV_COMPOSE) run --rm web $(CONTAINER_UV_RUN) python -m mypy .
