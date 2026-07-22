# Migração Makefile → Taskfile

## Objetivo

Trocar os 3 Makefiles do projeto por arquivos Taskfile (go-task.dev), que são feitos para serem usados como task runners ao contrário dos Makefiles que foram projetados para builds.

## Estrutura de arquivos

```
/
├── Taskfile.yml              # Root: includes + namespaces + setup global
├── service/
│   └── Taskfile.service.yml  # Service tasks (Docker Compose, quality, celery)
└── app/web/
    └── Taskfile.app.yml      # App tasks (Bun, quality, dev)
```

A raiz `Taskfile.yml` faz include dos dois arquivos filhos e cria os namespaces `service:` e `app:`.

## Targets mapeados

### Root (raiz)

| Comando | Descrição |
|---|---|
| `task` | Lista todas as tasks disponíveis (auto-gerado) |
| `task setup` | `docker compose build` em service + `bun install` em app/web |

### service (namespace `service:`)

**Dev:**

| Comando | Descrição |
|---|---|
| `task service:up` | Sobe stack dev com hot reload |
| `task service:down` | Derruba stack dev |
| `task service:build` | Rebuilda imagens dev |
| `task service:restart` | Reinicia stack dev |
| `task service:logs` | Logs da stack dev |
| `task service:ps` | Lista serviços dev |
| `task service:bash` | Shell no container web |
| `task service:shell` | Django shell |
| `task service:dbshell` | Django dbshell |
| `task service:psql` | psql no Postgres |
| `task service:migrate` | Aplica migrações |
| `task service:makemigrations` | Cria migrações |
| `task service:superuser` | Cria superuser |
| `task service:test` | Roda testes |
| `task service:collectstatic` | Coleta estáticos |
| `task service:manage CMD='...'` | Comando manage.py genérico |

**Celery:**

| Comando | Descrição |
|---|---|
| `task service:worker` | Celery worker |
| `task service:beat` | Celery beat |
| `task service:flower` | Flower |
| `task service:worker-logs` | Logs do worker |
| `task service:beat-logs` | Logs do beat |
| `task service:flower-logs` | Logs do flower |
| `task service:restart-worker` | Reinicia worker |
| `task service:restart-beat` | Reinicia beat |
| `task service:restart-flower` | Reinicia flower |

**Produção:**

| Comando | Descrição |
|---|---|
| `task service:prod` | Sobe stack prod |
| `task service:prod-down` | Derruba stack prod |
| `task service:prod-build` | Rebuilda imagens prod |
| `task service:prod-restart` | Reinicia stack prod |
| `task service:prod-logs` | Logs prod |
| `task service:prod-ps` | Lista serviços prod |
| `task service:prod-bash` | Shell prod |
| `task service:prod-shell` | Django shell prod |
| `task service:prod-dbshell` | dbshell prod |
| `task service:prod-psql` | psql prod |
| `task service:prod-migrate` | Migrações prod |
| `task service:prod-makemigrations` | Cria migrações prod |
| `task service:prod-superuser` | Superuser prod |
| `task service:prod-test` | Testes prod |
| `task service:prod-collectstatic` | Estáticos prod |
| `task service:prod-manage CMD='...'` | manage.py prod |
| `task service:prod-worker-logs` | Logs worker prod |
| `task service:prod-beat-logs` | Logs beat prod |
| `task service:prod-flower-logs` | Logs flower prod |
| `task service:prod-restart-worker` | Reinicia worker prod |
| `task service:prod-restart-beat` | Reinicia beat prod |
| `task service:prod-restart-flower` | Reinicia flower prod |

**Qualidade:**

| Comando | Descrição |
|---|---|
| `task service:lint` | Ruff check |
| `task service:format` | Ruff check --fix + format |
| `task service:typecheck` | Mypy |
| `task service:check` | Lint + format check + mypy |
| `task service:test-ci` | Pytest (modo CI) |
| `task service:coverage` | Pytest com cobertura |
| `task service:function-length` | Flake8 function-length |
| `task service:duplication` | JSCPD duplication |
| `task service:migration-check` | Django makemigrations --check (skip local, CI only) |
| `task service:contract-check` | OpenAPI contract diff |
| `task service:quality` | Todos os checks de qualidade |

### app (namespace `app:`)

| Comando | Descrição |
|---|---|
| `task app:dev` | Development server (bun run dev) |
| `task app:build` | Build Next.js (bun run build) |
| `task app:install` | Instala dependências (bun install) |
| `task app:lint` | ESLint (bun run lint) |
| `task app:lint-fix` | ESLint --fix |
| `task app:lint-fix-unsafe` | ESLint --fix --unsafe-fixes |
| `task app:typecheck` | TypeScript (bun run typecheck) |
| `task app:test` | Testes (bun run test) |
| `task app:coverage` | Testes com cobertura |
| `task app:quality` | Todos os checks de qualidade |
| `task app:generate-api-types` | Gera tipos da API |

## Targets removidos (limpeza)

- `help` manual → Taskfile gera automaticamente com `task --list`
- `repo-help` → redundante com `task --list`
- `setup` do service → movido para `task setup` global
- `setup-dev`, `up-dev`, `down-dev`, etc. → eram aliases, agora só `task service:up`, `task service:down`, etc.
- `setup` do app → movido para `task setup` global
- `install` do app → movido para `task setup` global

## Notas de implementação

- **CI não usa Makefiles** — as workflows do GitHub Actions chamam comandos diretamente. Nenhuma alteração CI necessária.
- **CLAUDE.md** precisa ser atualizado: trocar referências de `make` por `task`.
- **Instalação do Taskfile**: adicionar instruções no CLAUDE.md (go-task.dev).
- **Aliases do Makefile**: o Makefile de service tem muitos aliases `-dev` redundantes (ex: `up-dev: up`). No Taskfile, o namespace `service:` já implica dev. Os targets de produção usam prefixo `prod-`.
- **Variáveis**: `CMD='...'` no Makefile vira `task service:manage CMD='check'` no Taskfile (via `vars:`).
- **Docker Compose**: manter as variáveis `DEV_COMPOSE` e `PROD_COMPOSE` como `vars` no Taskfile.
