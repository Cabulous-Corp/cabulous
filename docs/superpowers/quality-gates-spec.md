# Design dos Quality Gates de CI do Cabulous

**Pipeline:** `cabulous-20260720-215306`
**Status:** design aprovado no Discord; aguardando revisão desta especificação escrita
**Branch base:** `develop`

## Objetivo

Implementar o programa completo de quality gates para o monorepo Cabulous, composto por Django/Python e Next.js/TypeScript. Toda a infraestrutura das fases 1 a 3 será entregue agora, mas a aplicação dos bloqueios seguirá a política granular aprovada: verificações determinísticas de segurança e integração bloqueiam imediatamente; verificações ruidosas ou caras permanecem observacionais ou agendadas até promoção explícita.

## Estado atual

O workflow atual do GitHub executa somente Ruff e mypy em `service/`. Ele não executa testes de backend, lint/type-check/build/testes de frontend, varredura de segredos ou dependências, validação de migrations, limites de duplicação ou tamanho de funções, comparação de contrato, SAST, E2E, mutation testing, CodeQL ou Scorecard.

O relatório concluído em `docs/superpowers/research/2026-07-20-multiagent-ci-quality-gates.md` é a fonte de evidências e recomenda baseline + ratchet, em vez de uma limpeza global imediata.

## Política de rollout

### Bloqueantes imediatamente em pull requests

- Ruff, formatação e mypy do backend;
- ESLint, TypeScript com `--noEmit` e build Next.js do frontend;
- `makemigrations --check --dry-run` e plano de migrations do Django;
- varredura de segredos com Gitleaks;
- Dependency Review e vulnerabilidades alta/crítica introduzidas, verificadas por OSV;
- comparação do contrato OpenAPI com baseline commitado, exceto waiver versionado e explícito para quebra intencional;
- violações novas ou ampliadas de tamanho de função e duplicação contra os baselines commitados.

### Observacionais antes de promoção posterior

- findings do Semgrep, inicialmente publicados e triados; apenas regras estáveis, de alta confiança, serão bloqueantes após aprovação explícita;
- checks de integração/E2E, inicialmente executados com artefatos e evidência de flake; a promoção exige ambiente reproduzível e aprovação explícita;
- métricas de cobertura e ratchet, inicialmente com baseline e sem regressão no escopo alterado, sem exigir limpeza histórica.

### Apenas agendados ou seletivos

- mutation testing Python e TypeScript em domínios críticos alterados;
- CodeQL;
- OpenSSF Scorecard;
- varreduras históricas/periódicas de segurança e relatórios caros.

## Arquitetura

Um único workflow `quality.yml` se torna o ponto de entrada de CI sensível a caminhos, com jobs independentes de backend, frontend, segurança, contrato e relatórios. Arquivos de configuração no repositório definem baseline legível para dívida de qualidade preexistente e exclusões estritas. O workflow publica artefatos JUnit, cobertura, scanners e contratos.

Todos os comandos serão expostos pelos Makefiles raiz, backend e frontend, para que agentes e desenvolvedores executem localmente as mesmas verificações do CI. O CI instala somente ferramentas declaradas/fixadas pelo projeto e usa dependências efêmeras quando necessárias.

## Definição dos gates

### Tamanho de funções e complexidade

- Python: Flake8 com `flake8-max-function-length`, configurado para 50 linhas físicas de código; migrations Django e arquivos explicitamente gerados recebem exclusão estreita.
- TypeScript/TSX: ESLint `max-lines-per-function` em 50, ignorando linhas vazias/comentários e contando corpo JSX.
- Complexidade Python: Ruff C901 com McCabe máximo 10 para código novo/alterado.
- Violações existentes ficam no baseline commitado. Um PR falha se adicionar violação ou aumentar violação já listada.

### Duplicação

`jscpd` analisa Python, TypeScript e TSX com `min-lines: 5` e `min-tokens: 70`. Somente migrations, declarações, arquivos gerados e saída de build são excluídos. O baseline permite dívida existente, mas bloqueia clone novo, clone existente ampliado ou mais de 3% de linhas duplicadas novas em arquivo alterado.

### Testes e cobertura

- O backend recebe pytest, pytest-django, pytest-cov e cobertura de branch. A cobertura total inicial será baselined; código alterado não poderá reduzi-la. O sinal global inicial será 35%.
- O frontend recebe Vitest e relatório de cobertura. A cobertura total inicial será baselined; código alterado não poderá reduzi-la. O sinal global inicial será 20%.
- Novo comportamento de domínio e toda correção de regressão exigem testes comportamentais. E2E inicia como suíte Playwright observacional para autenticação, fluxo principal de criação/atualização e autorização.

### Segurança e cadeia de suprimentos

- Gitleaks bloqueia segredos novos sem supressão válida.
- OSV e GitHub Dependency Review bloqueiam vulnerabilidades alta/crítica introduzidas.
- Semgrep começa observacional e publica SARIF/findings.
- CodeQL e Scorecard rodam agendados e publicam artefatos.

### Contratos e migrations

O backend gera OpenAPI JSON determinístico. Um baseline commitado é comparado com `oasdiff`; diferença breaking falha no PR, salvo waiver versionado contendo proprietário, justificativa e expiração. Tipos de API do frontend são comparados ou regenerados deterministicamente a partir do mesmo schema. As verificações de criação e plano de migrations Django bloqueiam imediatamente.

## Erros, exceções e tratamento

- Falha de scanner ou serviço de dependência nunca é tratada como sucesso; o job relevante informa falha de infraestrutura.
- Isenção de arquivo gerado exige marcador no arquivo ou entrada explícita e estreita de configuração; glob de domínio inteiro é proibido.
- Supressão de segurança exige ID da regra, proprietário, motivo, issue e expiração máxima de 90 dias.
- Waiver de contrato exige versão da API afetada, proprietário, justificativa, notas de compatibilidade/migração e expiração.
- E2E é reexecutado uma vez e publica trace, vídeo e logs; a segunda falha permanece visível, mas não bloqueia merge enquanto estiver observacional.

## Critérios de aceite

1. Todos os checks configurados possuem comandos equivalentes nos Makefiles e no CI.
2. Uma função nova/alterada de 51 linhas falha em Python e TypeScript/TSX; migrations e arquivos gerados válidos não falham.
3. Um clone de no mínimo 5 linhas e 70 tokens que piora o baseline falha.
4. Lint/tipos/build/testes de backend e frontend produzem relatórios legíveis por máquina e artefatos de cobertura.
5. Migration ausente, segredo novo, vulnerabilidade alta/crítica nova, build falhando ou quebra OpenAPI sem waiver válido bloqueiam PR.
6. Semgrep e E2E executam e publicam evidências sem bloquear até seus critérios separados de promoção serem aprovados.
7. Mutation tests, CodeQL e Scorecard executam somente em caminhos seletivos/agendados configurados.
8. Filtros por caminho e caches mantêm o caminho rápido de PR dentro da meta de 12 minutos p95 definida na pesquisa, medida por telemetria do workflow.
9. A entrega final inclui documentação, comandos verificados, revisão independente, verificação de integração e relatório final anexado no Discord.

## Não objetivos

- Forçar limpeza imediata de dívida histórica de cobertura, duplicação, complexidade ou tamanho de funções.
- Tratar cobertura como única evidência de comportamento.
- Promover gates observacionais automaticamente sem aprovação explícita.
- Substituir revisão humana, threat modeling ou testes exploratórios.
