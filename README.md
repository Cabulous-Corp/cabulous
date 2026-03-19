# cabulous monorepo

Monorepo principal do Cabulous Site.

Este repositorio concentra os projetos que compoem a plataforma da Cabulous, voltada para utilitarios e para guardar memorias da Cabulous Gang.

## Estrutura

- `service`: backend Django, API, admin e servicos assíncronos
- `app`: frontend do site, em Next.js

## Diretorios

### `service`

Aplicacao backend em Django responsavel por:

- API
- Django Admin
- Celery
- Celery Beat
- Flower
- integracao com Postgres e Redis

Documentacao especifica do backend:

- [README do service](service/README.md)

### `app`

Aplicacao frontend do Cabulous Site, destinada a ser desenvolvida em Next.js.

Documentacao especifica do frontend:

- [README do app](app/README.md)

## VS Code

Este monorepo foi pensado para ser aberto na pasta raiz no VS Code, permitindo visualizar lado a lado:

- o backend em `service`
- o frontend em `app`

As configuracoes do workspace ficam em [`.vscode/settings.json`](.vscode/settings.json), com:

- interpretador Python apontando para o ambiente virtual do backend em `service/.venv`
- Prettier como formatter padrao para arquivos TypeScript e JavaScript

## Fluxo esperado

Durante o desenvolvimento:

- o backend roda a partir de `service`
- o frontend roda a partir de `app`
- cada aplicacao pode ter sua propria documentacao, scripts e fluxo de execucao
