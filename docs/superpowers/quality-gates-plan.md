# Plano de Implementação dos Quality Gates do Cabulous

> **Para agentes:** use `using-superpowers`, TDD e verificação antes de concluir cada card.

**Objetivo:** Entregar toda a infraestrutura de quality gates do Cabulous, com bloqueios imediatos somente para checks determinísticos e gates caros/ruidosos configurados como observacionais ou agendados.

**Arquitetura:** O workflow `.github/workflows/quality.yml` será dividido em jobs independentes por domínio. Makefiles expõem os mesmos comandos localmente. Arquivos de baseline e de exceção versionada permitem ratchet sem ocultar dívida nova.

**Tecnologias:** GitHub Actions, uv/Python 3.13, Ruff, mypy, pytest, coverage, Flake8, jscpd, Bun, ESLint, TypeScript, Vitest, Playwright, Gitleaks, OSV, Semgrep, oasdiff, CodeQL e Scorecard.

## Restrições globais

- Função nova/alterada: máximo 50 linhas; migrations e arquivos explicitamente gerados são excluídos.
- Duplicação: `jscpd` com mínimo de 5 linhas e 70 tokens; bloqueia clone novo/ampliado e >3% de linhas novas duplicadas no arquivo alterado.
- Não reduzir cobertura baselined do escopo alterado; sinal global inicial: backend 35%, frontend 20%.
- Segredos, migrations, build, contrato OpenAPI e vulnerabilidades alta/crítica novas bloqueiam PR.
- Semgrep e E2E publicam evidência inicialmente; mutation, CodeQL e Scorecard são seletivos/agendados.

---

### Tarefa 1: Fundar comandos e baselines locais do backend

**Arquivos:**
- Modificar: `service/pyproject.toml`, `service/Makefile`, `Makefile`
- Criar: `service/pytest.ini`, `quality/baselines/python-function-length.json`, `quality/baselines/python-coverage.json`, `quality/README.md`
- Testar: `service/tests/quality/test_quality_commands.py`

- [ ] Escrever teste que invoca `make service quality` e valida que os subcomandos de lint, formato, tipos, pytest/cobertura, tamanho de função, duplicação e migration-check estão registrados.
- [ ] Executar `uv run pytest tests/quality/test_quality_commands.py -q`; confirmar falha antes dos targets/dependências.
- [ ] Adicionar aos grupos dev: `pytest`, `pytest-django`, `pytest-cov`, `flake8`, `flake8-max-function-length`; configurar `max-function-length = 50`, C901=10 e cobertura branch.
- [ ] Adicionar targets `test-ci`, `coverage`, `function-length`, `migration-check`, `quality` ao Makefile de `service`, e encaminhamento documentado no Makefile raiz.
- [ ] Gerar baselines por comando, documentar formato/atualização e rodar `make service quality`; confirmar exit 0 no baseline atual.
- [ ] Commit: `chore(quality): add backend quality commands and baselines`.

### Tarefa 2: Fundar comandos e baselines locais do frontend

**Arquivos:**
- Modificar: `app/web/package.json`, `app/web/Makefile`, `app/web/eslint.config.*`
- Criar: `app/web/vitest.config.ts`, `app/web/tests/quality/config.test.ts`, `quality/baselines/frontend-coverage.json`

- [ ] Escrever `config.test.ts` verificando que Vitest coleta testes e que ESLint aplica `max-lines-per-function: 50` a `.ts`/`.tsx`.
- [ ] Executar `bun run test`; confirmar falha antes de adicionar script/configuração.
- [ ] Adicionar `vitest`, provider de cobertura e scripts `typecheck`, `test`, `test:coverage`, `quality`.
- [ ] Configurar ESLint para ignorar somente artefatos/mocks gerados e aplicar a regra a código de produto.
- [ ] Adicionar targets `typecheck`, `test`, `coverage`, `quality` ao Makefile e gerar baseline de cobertura de 20%.
- [ ] Executar `make app quality`; confirmar lint, typecheck, build e testes com exit 0.
- [ ] Commit: `chore(quality): add frontend quality commands and baselines`.

### Tarefa 3: Implementar duplicação, ratchet e políticas de exceção

**Arquivos:**
- Criar: `.jscpd.json`, `quality/baselines/jscpd.json`, `quality/exceptions/security-suppressions.yaml`, `quality/exceptions/openapi-waivers.yaml`, `scripts/quality/compare-baseline.py`
- Testar: `scripts/quality/tests/test_compare_baseline.py`

- [ ] Escrever testes para `compare-baseline.py`: violação nova falha, violação existente inalterada passa, crescimento de violação falha e exceção expirada falha.
- [ ] Executar `python scripts/quality/tests/test_compare_baseline.py`; confirmar falha antes do script.
- [ ] Implementar leitor JSON/YAML e comparação determinística; rejeitar entradas sem proprietário, justificativa, issue e expiração (máximo de 90 dias para segurança).
- [ ] Configurar jscpd com Python/TS/TSX, limiares aprovados e exclusões estritas; gerar baseline inicial.
- [ ] Rodar jscpd e testes do comparador; confirmar saída de relatório JSON e exit 0 contra baseline.
- [ ] Commit: `feat(quality): enforce duplication and baseline ratchets`.

### Tarefa 4: Implementar contrato OpenAPI, migrations e artefatos de testes

**Arquivos:**
- Criar: `service/scripts/export_openapi.py`, `quality/openapi/baseline.json`, `scripts/quality/check-openapi.sh`
- Modificar: `service/Makefile`, `app/web/Makefile`, `app/web/package.json`
- Testar: `service/tests/quality/test_openapi_export.py`

- [ ] Escrever teste garantindo export OpenAPI determinístico e JSON válido.
- [ ] Executar o teste; confirmar falha antes do exportador.
- [ ] Implementar exportador com configuração Django e gerar `quality/openapi/baseline.json`.
- [ ] Adicionar `contract-check` que usa `oasdiff breaking` e valida waiver versionado (API, owner, motivo, compatibilidade, expiração).
- [ ] Adicionar `migration-check` com `python manage.py makemigrations --check --dry-run` e `showmigrations --plan`.
- [ ] Executar export, comparison, migration-check e geração de tipos frontend; confirmar exit 0.
- [ ] Commit: `feat(quality): add API contract and migration gates`.

### Tarefa 5: Reestruturar o GitHub Actions para gates bloqueantes e observacionais

**Arquivos:**
- Modificar: `.github/workflows/quality.yml`
- Criar: `.github/workflows/codeql.yml`, `.github/workflows/scorecard.yml`, `.github/workflows/quality-scheduled.yml`
- Testar: `scripts/quality/tests/test_workflow_contract.py`

- [ ] Escrever teste estrutural YAML: jobs bloqueantes não usam `continue-on-error`; Semgrep/E2E usam `continue-on-error`; jobs pesados têm gatilho schedule/workflow_dispatch.
- [ ] Executar o teste; confirmar falha contra workflow atual de job único.
- [ ] Criar jobs cacheados e path-aware de backend, frontend, duplication/function-size, secrets, dependências, migration e OpenAPI; publicar JUnit/cobertura/JSON como artefatos.
- [ ] Adicionar Semgrep e Playwright observacionais com trace/vídeo/log; falha de infraestrutura deve ser visível.
- [ ] Adicionar CodeQL, Scorecard e mutation testing com schedule e `workflow_dispatch`; mutation só executa em domínio crítico selecionado.
- [ ] Validar YAML, testes estruturais e comandos locais correspondentes.
- [ ] Commit: `ci: add phased quality-gate workflows`.

### Tarefa 6: Exercitar gates com fixtures e documentar a operação

**Arquivos:**
- Criar: `quality/fixtures/over-limit.py`, `quality/fixtures/duplicate-a.ts`, `quality/fixtures/duplicate-b.ts`, `docs/quality-gates.md`
- Modificar: `README.md`
- Testar: `scripts/quality/tests/test_gate_fixtures.sh`

- [ ] Escrever script de aceitação que cria cópia temporária de fixture, roda cada gate e exige falha para: função de 51 linhas, clone novo, migration ausente, segredo de teste autorizado somente na fixture e quebra de contrato sem waiver.
- [ ] Executar script antes das fixtures/configuração final; confirmar falha controlada.
- [ ] Implementar fixtures isoladas/excluídas da varredura de produção e o script que altera cópia temporária, nunca o repositório de trabalho.
- [ ] Documentar comandos locais, interpretação de artefatos, baseline/ratchet, criação/expiração de waiver e política de promoção de Semgrep/E2E.
- [ ] Rodar o conjunto completo: backend quality, frontend quality, workflow tests e fixtures; confirmar evidência exit 0.
- [ ] Commit: `docs: document CI quality gates operation`.

## Verificação final

1. `make service quality`
2. `make app quality`
3. `python scripts/quality/tests/test_compare_baseline.py`
4. `python scripts/quality/tests/test_workflow_contract.py`
5. `bash scripts/quality/tests/test_gate_fixtures.sh`
6. Validar YAML dos quatro workflows e confirmar que nenhum artefato/credencial de ambiente foi commitado.
7. Revisão independente de cada tarefa, integração serial, revisão final e anexo do relatório final no Discord.
