# cabulous service

Backend Django do Cabulous Site.

Este diretorio concentra a API, o painel administrativo e os servicos de backend usados pelo site da Cabulous, uma plataforma voltada para utilitarios e para guardar memorias da Cabulous Gang.

## Stack

- Django
- Django REST Framework
- Celery
- Flower
- Postgres 17
- Redis
- Docker Compose
- `uv` para dependencias Python
- `pydantic-settings` para configuracao
- Jazzmin para modernizacao do Django Admin

## Objetivo do projeto

Esta aplicacao backend existe para sustentar o ecossistema do Cabulous Site, oferecendo:

- API para os recursos do site
- painel administrativo com Django Admin
- processamento de tarefas assíncronas com Celery
- agendamentos com Celery Beat
- monitoramento do Celery com Flower
- persistencia de dados com Postgres
- cache e broker com Redis

## Importante

Os comandos do backend devem ser executados a partir deste diretorio `service`.

Exemplo:

```bash
cd service
make up-dev
```

## Ambiente de desenvolvimento

O fluxo principal documentado neste projeto e o de desenvolvimento local com Docker.

No modo de desenvolvimento:

- a aplicacao web sobe com autoreload do Django
- o `worker` do Celery reinicia automaticamente quando arquivos Python mudam
- o `beat` do Celery reinicia automaticamente quando arquivos Python mudam
- o Flower tambem roda com reinicio automatico quando arquivos Python mudam
- as migracoes sao aplicadas automaticamente na subida da aplicacao web

## Setup

### Requisitos

- Docker
- Docker Compose
- `make` instalado no sistema

### Subida do ambiente

Comandos minimos para subir o backend em desenvolvimento:

1. Copiar o arquivo de ambiente:

```bash
cp .env.example .env
```

No Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

2. Subir a stack:

```bash
make up-dev
```

Aambiente de desenvolvimento de pé!

### VS Code (recomendado)

Para completar o setup de desenvolvimento no VS Code:

1. Abrir o Command Palette com `F1` ou `Ctrl+Shift+P`
2. Executar `Python: Select Interpreter`
3. Selecionar o interpretador recomendado do projeto (`service/.venv`)
4. Instalar as extensoes recomendadas do workspace (`.vscode/extensions.json`)

Com isso, lint, formatacao e analise de codigo ficam configurados corretamente.

## Servicos disponiveis

Ao subir o ambiente de desenvolvimento, os principais servicos ficam disponiveis assim:

- aplicacao Django: [http://localhost:8000](http://localhost:8000)
- Django Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- healthcheck da API: [http://localhost:8000/api/health/](http://localhost:8000/api/health/)
- Flower: [http://localhost:5555](http://localhost:5555)
- Postgres exposto localmente na porta `5433`
- Redis exposto localmente na porta `6380`

## Estrutura da stack

Os servicos principais da stack sao:

- `web`: aplicacao Django
- `worker`: processamento de tarefas assíncronas
- `beat`: agendador do Celery
- `flower`: painel de monitoramento do Celery
- `db`: banco Postgres
- `redis`: cache e broker

## Configuracao

As configuracoes da aplicacao sao centralizadas com `pydantic-settings`.

O arquivo [`.env.example`](.env.example) mostra os valores esperados para:

- aplicacao Django
- banco de dados
- Redis
- Celery
- Flower

## Dependencias Python

As dependencias sao gerenciadas com `uv`.

Quando for necessario sincronizar o ambiente Python fora dos containers, use:

```bash
uv sync
```

## Comandos do projeto

Os comandos de operacao e desenvolvimento estao organizados no [Makefile](Makefile).

Para ver a lista disponivel:

```bash
make help
```
