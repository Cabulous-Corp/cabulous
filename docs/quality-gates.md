# Quality Gates do Cabulous

## Visao Geral

O Cabulous possui um sistema de quality gates que garante que violacoes de qualidade nao entrem no codigo principal. Os gates sao executados localmente durante o desenvolvimento e no CI (GitHub Actions) em cada pull request e push para develop/main.

## Comandos Locais

### Backend (service/)

```bash
# Todos os checks de qualidade de uma vez
task service:quality

# Individualmente:
task service:lint            # Ruff check + format check
task service:typecheck       # Mypy
task service:test-ci         # Pytest
task service:coverage        # Cobertura com pytest-cov
task service:function-length # Flake8 C901/MFL000 (max 50 linhas)
task service:duplication     # jscpd (duplicacao de codigo)
task service:contract-check  # Comparacao OpenAPI vs baseline
```

### Frontend (app/web/)

```bash
# Todos os checks de qualidade de uma vez
task app:quality

# Individualmente:
task app:lint        # ESLint
task app:typecheck   # tsc --noEmit
task app:test        # Vitest
task app:coverage    # Vitest com cobertura
```

## Interpretacao de Artefatos

### Baselines (`quality/baselines/`)

| Arquivo | O que controla |
|---------|---------------|
| `jscpd.json` | Total de clones, linhas duplicadas, percentual, e lista de duplicatas conhecidas |

Os limites reais de cobertura e tamanho de funcao vivem em `service/pyproject.toml`
(`[tool.coverage.report]` e `[tool.flake8]`) e na configuracao do Vitest em `app/web/`,
nao em arquivos de baseline separados.

### Excecoes (`quality/exceptions/`)

| Arquivo | O que controla |
|---------|---------------|
| `openapi-waivers.yaml` | Waivers para mudancas contratuais breaking no OpenAPI |
| `security-suppressions.yaml` | Supressoes para findings de seguranca (max 90 dias) |

### OpenAPI (`quality/openapi/`)

| Arquivo | O que controla |
|---------|---------------|
| `baseline.json` | Schema OpenAPI commitado que define o contrato atual |

### Relatorios CI (artefatos)

| Artefato | Job CI |
|----------|--------|
| `jscpd-report/` (jscpd) | backend-duplication |
| `coverage.json` (pytest) | backend-test |
| `semgrep.sarif` | semgrep |
| `migration-check.txt` | backend-migration |
| `report.xml` (JUnit) | backend-test |

## Ratchet: Como Funciona

O ratchet e o mecanismo que impede que metricas de qualidade piorem.

### Regra fundamental

**Metricas so podem melhorar ou ficar iguais. Qualquer piora falha no gate.**

### Duplicacao (jscpd)

O baseline em `quality/baselines/jscpd.json` define:
- `total_duplicates`: total de clones (nao pode aumentar)
- `total_duplicated_lines`: linhas duplicadas (nao pode aumentar)
- `known_duplicates`: lista de duplicatas ja conhecidas (aceitas)
- `max_new_lines_in_changed_file_pct`: maximo de novas linhas duplicadas em um arquivo alterado (3%)

Se um PR introduz novas duplicatas ou amplia duplicatas existentes, o gate falha.

### Para atualizar o baseline

1. Execute a verificacao local: `task service:duplication`
2. Analise se as novas violacoes sao aceitaveis
3. Atualize o JSON em `quality/baselines/jscpd.json`
4. Commit o baseline junto com a mudanca de codigo

## Waivers: Criacao e Expiracao

### Waivers OpenAPI

Quando uma mudanca breaking no contrato OpenAPI e necessaria:

1. Crie uma entrada em `quality/exceptions/openapi-waivers.yaml`:

```yaml
- api_version: v1
  owner: seu@email.com
  justification: Motivo da mudanca breaking
  compatibility_notes: Como migrar (ex: redirecionamento 308)
  expires: "2026-10-01"  # Data de expiracao obrigatoria
```

2. O gate de contrato aceita a mudanca enquanto houver waiver ativo
3. Apos a expiracao, o waiver e rejeitado e o gate volta a bloquear

### Supressoes de Seguranca

Para suprimir um finding de seguranca (ex: gitleaks):

1. Crie uma entrada em `quality/exceptions/security-suppressions.yaml`:

```yaml
- rule_id: gitleaks-generic-api-key
  owner: seu@email.com
  reason: Chave de teste em fixture, nao vai para producao
  issue_url: https://github.com/Cabulous-Corp/cabulous/issues/42
  expires: "2026-10-01"  # Maximo 90 dias a partir de hoje
```

2. **Limite rigido**: expiracao maxima de 90 dias a partir da data de criacao
3. Expiracoes de waivers OpenAPI sao validadas por `scripts/quality/check-openapi.sh`
   durante o `backend-contract`; supressoes de seguranca sao revisadas manualmente
   (os gates de seguranca gitleaks/semgrep sao observacionais).

### Regras de Expiracao

| Tipo | Limite | Validacao |
|------|--------|-----------|
| Waiver OpenAPI | Sem limite fixo | `check-openapi.sh` (data futura) |
| Supressao Seguranca | Max 90 dias | Revisao manual |
| Ambos | Obrigatorio ter `expires` | Campo nao pode ser vazio |

## Promocao: Semgrep e E2E

### Semgrep (Observational)

- **Status**: observacional (nao bloqueia PR)
- **Configuracao**: `continue-on-error: true` no workflow
- **Artefato**: `semgrep.sarif` (SARIF format)
- **Promocao para blocking**: quando o time tiver processo para remediar findings

### E2E Tests (Observational)

- **Status**: observacional (nao bloqueia PR)
- **Configuracao**: `continue-on-error: true` (quando implementado)
- **Promocao para blocking**: quando houver suite E2E estavel e cobertura adequada

### Quando promover um gate de observacional para blocking

1. O gate deve ter zero falsos positivos por 2 semanas seguidas
2. O time deve ter processo para remediar violacoes em < 24h
3. A cobertura do gate deve ser >= 90% dos cenarios criticos
4. Documentar a decisao no commit de promocao

## Workflows CI

### quality.yml (Pull Request / Push)

Jobs bloqueantes (falham o PR):
- `backend-lint`, `backend-typecheck`, `backend-test`
- `backend-duplication`, `backend-contract`, `backend-migration`
- `frontend-lint`, `frontend-typecheck`, `frontend-build`, `frontend-test`

Jobs observacionais (nao falham o PR):
- `semgrep`

### codeql.yml e scorecard.yml

- Executados apenas via schedule + workflow_dispatch
- Pesados: nao devem rodar em cada PR
