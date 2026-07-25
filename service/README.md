# cabulous service

Backend Django do Cabulous Site.

Este diretorio concentra a API, o painel administrativo e os servicos de backend usados pelo site da Cabulous, uma plataforma voltada para utilitarios e para guardar memorias da Cabulous Gang.

## Stack

- Django
- Django REST Framework
- Celery
- Flower
- MinIO
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
- armazenamento de arquivos com bucket S3 self-hosted (MinIO)
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
- `uv` instalado no sistema

### Subida do ambiente

## Cabulous Events API

Three Django apps support the events feature:

| App | Prefix | Responsibility |
|---|---|---|
| `media` | `/api/media/` | Photo upload (signed URL), CRUD, deletion from S3 |
| `events` | `/api/events/` | Event lifecycle (create/cancel/reactivate/restore), audiences, participants, photos, highlights |
| `comments` | `/api/comments/` | Threaded comments via GenericForeignKey on any target model |

### Upload flow (signed URL)

1. `POST /api/media/photos/upload-urls/` -- server returns presigned PUT URLs
2. Client uploads each file directly to S3 with `PUT`
3. `POST /api/media/photos/confirm/` -- server validates MIME, size, and prefix, then creates `Photo` rows

**Limits:** 25 MB per file, 50 files per request, image types only (`image/jpeg`, `image/png`, `image/gif`).

### Pagination

All list endpoints paginate at 20 items per page (DRF `PageNumberPagination`).

### Admin

All three apps register their models in Django Admin. The `events` admin includes an inline for photos, audiences, participants, location, and highlights, plus a "Restore selected events" bulk action that calls the `restore_event` lifecycle service.

## Comandos do projeto

Os comandos de operacao e desenvolvimento estao organizados no Makefile.

Para ver a lista disponivel:

```bash
make help
```
