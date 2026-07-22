# Quality Gates do Cabulous

## Visao Geral

O Cabulous possui um sistema de quality gates que garante que violacoes de qualidade nao entrem no codigo principal. Os gates sao executados localmente durante o desenvolvimento e no CI (GitHub Actions) em cada pull request e push para develop/main.

## Comandos Locais

### Backend (service/)

```bash
# Todos os checks de qualidade de uma vez
make service quality

# Individualmente:
make service lint          # Ruff check + format check
make service typecheck     # Mypy
make service test-ci       # Pytest
make service coverage      # Cobertura com pytest-cov
make service function-length  # Flake8 C901/MFL000 (max 50 linhas)
make service duplication      # jscpd (duplicacao de codigo)
make service contract-check   # Comparacao OpenAPI vs baseline
```

### Frontend (app/web/)

```bash
# Todos os checks de qualidade de uma vez
make app quality

# Individualmente:
make app lint        # ESLint
make app typecheck   # tsc --noEmit
make app test        # Vitest
make app test:coverage  # Vitest com cobertura
```

### Scripts de Qualidade (repo root)

```bash
# Comparar baseline de duplicacao com relatorio atual
python3 scripts/quality/compare-baseline.py \
    quality/baselines/jscpd.json \
    report.json

# Validar waivers de seguranca e OpenAPI
python3 scripts/quality/compare-baseline.py \
    quality/baselines/jscpd.json \
    report.json \
    --security-suppressions quality/exceptions/security-suppressions.yaml \
    --openapi-waivers quality/exceptions/openapi-waivers.yaml

# Executar testes dos gates (aceitacao)
bash scripts/quality/tests/test_gate_fixtures.sh

# Executar testes unitarios dos scripts de qualidade
python3 -m pytest scripts/quality/tests/ -v
```

## Interpretacao de Artefatos

### Baselines (`quality/baselines/`)

| Arquivo | O que controla |
|---------|---------------|
| `jscpd.json` | Total de clones, linhas duplicadas, percentual, e lista de duplicatas conhecidas |
| `python-function-length.json` | Max 50 linhas por funcao, complexidade McCabe max 10 |
| `python-coverage.json` | Cobertura minima branch 35% (atual: ~26%) |
| `frontend-coverage.json` | Cobertura minima 20% |

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
| `report.json` (jscpd) | backend-duplication |
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

Se um PR introduce novas duplicatas ou amplia duplicatas existentes, o gate falha.

### Para atualizar o baseline

1. Execute a verificacao local: `make service duplication`
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
3. Expiracoes sao validadas pelo script `compare-baseline.py`

### Regras de Expiracao

| Tipo | Limite | Validacao |
|------|--------|-----------|
| Waiver OpenAPI | Sem limite fixo | Deve ter data futura |
| Supressao Seguranca | Max 90 dias | Validado por `compare-baseline.py` |
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

### quality-scheduled.yml (Semanal)

- `mutation-backend`: testes de mutacao (Domingo 06:00 UTC)

### codeql.yml e scorecard.yml

- Executados apenas via schedule + workflow_dispatch
- Pesados: nao devem rodar em cada PR

## Fixtures de Teste

Os fixtures em `quality/fixtures/` sao usados para testar que os gates funcionam corretamente:

| Fixture | Gate testado | O que verifica |
|---------|-------------|----------------|
| `over-limit.py` | function-length | Funcao de 51 linhas (limite: 50) |
| `duplicate-a.ts` + `duplicate-b.ts` | duplication | Codigo clonado entre arquivos |

**Importante**: fixtures sao excluidos da varredura de producao:
- `.jscpd.json`: `**/fixtures/**` no ignore
- `pyproject.toml`: `*/fixtures/*` no extend-exclude do ruff

Para executar os testes de aceitacao:
```bash
bash scripts/quality/tests/test_gate_fixtures.sh
```
