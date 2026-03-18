COMPOSE = docker compose -f docker-compose.yaml
DEV_COMPOSE = docker compose -f docker-compose.yaml -f docker-compose.dev.yaml

MANAGE_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
MANAGE_CMD := $(strip $(if $(MANAGE_ARGS),$(MANAGE_ARGS),$(cmd)))

.PHONY: help
.PHONY: up down build restart logs ps bash shell dbshell psql migrate makemigrations superuser test collectstatic manage
.PHONY: worker-logs beat-logs flower-logs restart-worker restart-beat restart-flower
.PHONY: up-dev down-dev restart-dev logs-dev ps-dev bash-dev shell-dev dbshell-dev psql-dev migrate-dev makemigrations-dev superuser-dev test-dev manage-dev
.PHONY: worker-logs-dev beat-logs-dev flower-logs-dev restart-worker-dev restart-beat-dev restart-flower-dev
.PHONY: lint format

ifeq (manage,$(firstword $(MAKECMDGOALS)))
  ifneq ($(MANAGE_ARGS),)
    $(foreach arg,$(MANAGE_ARGS),$(eval $(arg):;@:))
  endif
endif

ifeq (manage-dev,$(firstword $(MAKECMDGOALS)))
  ifneq ($(MANAGE_ARGS),)
    $(foreach arg,$(MANAGE_ARGS),$(eval $(arg):;@:))
  endif
endif

help:
	@echo "Uso: make <target>"
	@echo ""
	@echo "# Producao"
	@echo "  make up                 - sobe a stack completa"
	@echo "  make down               - derruba a stack"
	@echo "  make build              - rebuilda as imagens"
	@echo "  make restart            - reinicia a stack"
	@echo "  make logs               - acompanha logs da aplicacao web"
	@echo "  make ps                 - lista os servicos"
	@echo "  make bash               - abre shell no container web"
	@echo "  make shell              - abre o shell do Django"
	@echo "  make dbshell            - abre o dbshell do Django"
	@echo "  make psql               - abre o psql no Postgres"
	@echo "  make migrate            - aplica migracoes"
	@echo "  make makemigrations     - cria migracoes"
	@echo "  make superuser          - cria um superusuario"
	@echo "  make test               - roda os testes"
	@echo "  make collectstatic      - coleta arquivos estaticos"
	@echo "  make manage check       - roda comando arbitrario do manage.py"
	@echo ""
	@echo "# Producao Celery"
	@echo "  make worker-logs        - logs do celery worker"
	@echo "  make beat-logs          - logs do celery beat"
	@echo "  make flower-logs        - logs do flower"
	@echo "  make restart-worker     - recria o worker"
	@echo "  make restart-beat       - recria o beat"
	@echo "  make restart-flower     - recria o flower"
	@echo ""
	@echo "# Desenvolvimento"
	@echo "  make up-dev             - sobe a stack dev com hot reload"
	@echo "  make down-dev           - derruba a stack dev"
	@echo "  make restart-dev        - reinicia a stack dev"
	@echo "  make logs-dev           - acompanha todos os logs da stack dev"
	@echo "  make ps-dev             - lista os servicos da stack dev"
	@echo "  make bash-dev           - abre shell no web da stack dev"
	@echo "  make shell-dev          - abre o shell do Django na stack dev"
	@echo "  make dbshell-dev        - abre o dbshell do Django na stack dev"
	@echo "  make psql-dev           - abre o psql no Postgres da stack dev"
	@echo "  make migrate-dev        - aplica migracoes na stack dev"
	@echo "  make makemigrations-dev - cria migracoes na stack dev"
	@echo "  make superuser-dev      - cria superusuario na stack dev"
	@echo "  make test-dev           - roda testes na stack dev"
	@echo "  make manage-dev check   - roda comando arbitrario do manage.py na stack dev"
	@echo ""
	@echo "# Desenvolvimento Celery"
	@echo "  make worker-logs-dev    - logs do worker na stack dev"
	@echo "  make beat-logs-dev      - logs do beat na stack dev"
	@echo "  make flower-logs-dev    - logs do flower na stack dev"
	@echo "  make restart-worker-dev - recria o worker na stack dev"
	@echo "  make restart-beat-dev   - recria o beat na stack dev"
	@echo "  make restart-flower-dev - recria o flower na stack dev"
	@echo ""
	@echo "# Qualidade"
	@echo "  make lint               - roda o ruff"
	@echo "  make format             - aplica autofix do ruff"

# Prod
up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

restart: down up

logs:
	$(COMPOSE) logs -f web

ps:
	$(COMPOSE) ps

bash:
	$(COMPOSE) exec web sh

shell:
	$(COMPOSE) run --rm web uv run python manage.py shell

dbshell:
	$(COMPOSE) run --rm web uv run python manage.py dbshell

psql:
	$(COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

migrate:
	$(COMPOSE) run --rm web uv run python manage.py migrate

makemigrations:
	$(COMPOSE) run --rm web uv run python manage.py makemigrations

superuser:
	$(COMPOSE) run --rm web uv run python manage.py createsuperuser

test:
	$(COMPOSE) run --rm web uv run python manage.py test

collectstatic:
	$(COMPOSE) run --rm web uv run python manage.py collectstatic --noinput

manage:
	$(COMPOSE) run --rm web uv run python manage.py $(MANAGE_CMD)

# Prod Celery
worker-logs:
	$(COMPOSE) logs -f worker

beat-logs:
	$(COMPOSE) logs -f beat

flower-logs:
	$(COMPOSE) logs -f flower

restart-worker:
	$(COMPOSE) up -d --build --force-recreate worker

restart-beat:
	$(COMPOSE) up -d --build --force-recreate beat

restart-flower:
	$(COMPOSE) up -d --build --force-recreate flower

# Dev
up-dev:
	$(DEV_COMPOSE) up --build -d

down-dev:
	$(DEV_COMPOSE) down

restart-dev: down-dev up-dev

logs-dev:
	$(DEV_COMPOSE) logs -f

ps-dev:
	$(DEV_COMPOSE) ps

bash-dev:
	$(DEV_COMPOSE) exec web sh

shell-dev:
	$(DEV_COMPOSE) run --rm web uv run python manage.py shell

dbshell-dev:
	$(DEV_COMPOSE) run --rm web uv run python manage.py dbshell

psql-dev:
	$(DEV_COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

migrate-dev:
	$(DEV_COMPOSE) run --rm web uv run python manage.py migrate

makemigrations-dev:
	$(DEV_COMPOSE) run --rm web uv run python manage.py makemigrations

superuser-dev:
	$(DEV_COMPOSE) run --rm web uv run python manage.py createsuperuser

test-dev:
	$(DEV_COMPOSE) run --rm web uv run python manage.py test

manage-dev:
	$(DEV_COMPOSE) run --rm web uv run python manage.py $(MANAGE_CMD)

# Dev Celery
worker-logs-dev:
	$(DEV_COMPOSE) logs -f worker

beat-logs-dev:
	$(DEV_COMPOSE) logs -f beat

flower-logs-dev:
	$(DEV_COMPOSE) logs -f flower

restart-worker-dev:
	$(DEV_COMPOSE) up -d --build --force-recreate worker

restart-beat-dev:
	$(DEV_COMPOSE) up -d --build --force-recreate beat

restart-flower-dev:
	$(DEV_COMPOSE) up -d --build --force-recreate flower

# Qualidade
lint:
	uv run ruff check .

format:
	uv run ruff check . --fix
