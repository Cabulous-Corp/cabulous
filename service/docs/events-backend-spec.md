# Cabulous Events API — Design Specification

Status: aguardando aprovação da spec escrita
Data: 2026-07-20
Pipeline: `cabulous-events-api-20260720-020614`
Issue: [Cabulous-Corp/cabulous#7](https://github.com/Cabulous-Corp/cabulous/issues/7)

## 1. Objetivo

Entregar o backend REST do módulo Cabulous Events. Usuários onboarded poderão criar e consultar eventos, gerenciar participantes, localização e audiences, associar fotos globais, escolher thumbnail, registrar highlights e conversar em comentários encadeados. A API também deverá preservar histórico por soft delete, manter status temporal consistente e fornecer uma galeria global de fotos com upload direto para MinIO.

## 2. Escopo

### Incluído

- CRUD, cancelamento, reativação, soft delete e restauração de eventos.
- Criador, participantes, tipo, múltiplos audiences e localização.
- Status persistido e reconciliado por tempo.
- Entidade global `Photo`, galeria e upload assinado em lote.
- Relação N:N entre eventos e fotos e escolha de thumbnail.
- Highlights com fotos do evento.
- Comentários genéricos por alvo tipado e threads ilimitadas.
- Paginação, ordenação, filtros, busca, permissões, Admin e testes.

### Fora do escopo

- Frontend e calendário visual.
- Notificações e lembretes.
- Recorrência e integração com calendários externos.
- Reações, likes ou votos.
- Marcação de usuários nas fotos.
- Processamento de imagem, thumbnails derivadas ou leitura de EXIF.
- Moderação com aprovação prévia.
- Alvos de comentário além de `events.Event`.

## 3. Arquitetura

A implementação será dividida em três apps Django:

- `events`: domínio do evento, audiences, participantes, localização, vínculos de fotos e highlights.
- `media`: fotos globais, signed URLs, confirmação de uploads, galeria e exclusão no storage.
- `comments`: comentários genéricos por alvo tipado e threads.

`events` depende de `media` para referenciar fotos. `comments` usa `django.contrib.contenttypes` e uma allowlist de alvos, sem depender de herança polimórfica. Regras que atravessam modelos serão implementadas em serviços transacionais e reutilizadas por serializers, views, Admin e tarefas. Os filtros declarativos serão implementados com `django-filter`, adicionado como dependência do backend.

## 4. Modelo de dados

### 4.1 Event

Campos:

- `id`: UUID.
- `title`: string obrigatória, até 255 caracteres, normalizada por trim.
- `description`: texto opcional.
- `start_at`: datetime obrigatório com timezone.
- `end_at`: datetime obrigatório com timezone e maior ou igual a `start_at`.
- `type`: um valor de `EventType`.
- `creator`: FK obrigatória para `User`, com proteção contra exclusão física.
- `status`: enum persistido `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
- `cancelled_at`: datetime opcional.
- `deleted_at`: datetime opcional para soft delete.
- `created_at`, `updated_at`.

O status esperado é:

- `CANCELLED` quando `cancelled_at` estiver preenchido;
- `SCHEDULED` quando agora for anterior a `start_at`;
- `IN_PROGRESS` quando `start_at <= agora <= end_at`;
- `COMPLETED` quando agora for posterior a `end_at`.

O status é corrigido em criação, alteração e leitura e por uma tarefa do Celery Beat executada a cada minuto. Cancelar, reativar e reconciliar são operações idempotentes.

A exclusão é lógica. O endpoint comum deixa de retornar o evento excluído. Criador e staff podem restaurá-lo.

### 4.2 EventAudience

Tabela associativa com:

- `event`: FK.
- `audience`: enum `ILUMINADOS`, `VOYEURS`, `ELETRONICOS`, `OTHERS`.
- timestamps.

Restrição única em `(event, audience)`. Todo evento deve ter pelo menos um audience. O antigo campo singular `public` será migrado para a nova relação sem alterar a migration inicial compartilhada.

### 4.3 EventParticipant

Tabela associativa com:

- `event`: FK.
- `user`: FK.
- `added_by`: FK opcional para `User`.
- `created_at`.

Restrição única em `(event, user)`. O criador entra automaticamente na criação do evento, mas pode ser removido da lista sem perder propriedade.

### 4.4 EventLocation

Relação 1:1 opcional com `Event`. Quando a localização for enviada, todos os campos abaixo são obrigatórios, exceto `complement`:

- `name`;
- `street`;
- `number`;
- `complement`, opcional;
- `neighborhood`;
- `city`;
- `state`, UF com duas letras;
- `postal_code`, CEP normalizado;
- `country`, padrão `BR`;
- `latitude`, entre -90 e 90;
- `longitude`, entre -180 e 180.

### 4.5 Photo

Entidade global no app `media`:

- `id`: UUID.
- `object_key`: chave única no storage.
- `uploader`: FK para `User`.
- `taken_on`: data obrigatória (`DateField`), sem restrição ao intervalo de qualquer evento.
- `caption`: texto opcional.
- metadados confirmados: `content_type`, `size_bytes`.
- `created_at`, `updated_at`.

Formatos aceitos: JPEG, PNG, WebP e GIF. Tamanho máximo real: 25 MB.

A exclusão é física: o objeto MinIO deve ser removido antes da exclusão do registro. Relações com eventos, thumbnail e highlights são removidas por cascata. Uma falha de storage mantém o banco inalterado e permite repetição idempotente.

### 4.6 EventPhoto

Tabela associativa no app `events`:

- `event`: FK.
- `photo`: FK.
- `linked_by`: FK para `User`.
- `is_thumbnail`: booleano.
- `created_at`.

Restrições:

- unicidade em `(event, photo)`;
- no máximo um registro `is_thumbnail=true` por evento.

Dessa forma, a thumbnail é sempre uma foto vinculada. Ela é opcional. A mesma foto pode ser vinculada a vários eventos.

### 4.7 Highlight e HighlightPhoto

`Highlight`:

- `id`: UUID.
- `event`: FK.
- `author`: FK para `User`.
- `text`: texto obrigatório, com no máximo 500 caracteres.
- timestamps.

`HighlightPhoto` liga highlights a fotos. O serviço exige que cada foto já esteja vinculada ao mesmo evento. Excluir um highlight é uma operação física e não exclui fotos.

### 4.8 Comment

Entidade no app `comments`:

- `id`: UUID.
- `author`: FK para `User`.
- `body`: texto obrigatório, com no máximo 5.000 caracteres.
- `target_content_type`: FK para `ContentType`.
- `target_object_id`: UUID.
- `target`: `GenericForeignKey`.
- `parent`: FK autorreferente opcional.
- `deleted_at`: soft delete.
- timestamps.

Índice composto em `(target_content_type, target_object_id)`. A allowlist inicial aceita somente `events.Event`. O alvo e o pai devem existir e estar ativos no momento da criação; pai e filho devem ter exatamente o mesmo alvo. `parent` é imutável após a criação para impedir ciclos.

Um comentário excluído mantém a posição na thread e é serializado como placeholder sem expor o corpo removido. Comentários de eventos excluídos permanecem no banco, mas não aparecem nas APIs comuns.

## 5. API REST

Todas as rotas exigem autenticação e onboarding concluído.

### 5.1 Eventos

- `GET /api/events/`
- `POST /api/events/`
- `GET /api/events/{event_id}/`
- `PATCH /api/events/{event_id}/`
- `DELETE /api/events/{event_id}/`
- `POST /api/events/{event_id}/cancel/`
- `POST /api/events/{event_id}/reactivate/`
- `POST /api/events/{event_id}/restore/`
- `GET /api/events/options/`

Criação e edição aceitam `audiences` como lista não vazia de enums e a localização opcional como objeto estruturado completo. `creator`, `status`, `cancelled_at`, `deleted_at` e timestamps são somente leitura nas operações CRUD comuns.

Listagem:

- paginação por número de página, 20 itens;
- padrão: todos os eventos ativos, incluindo cancelados, por `-start_at` e desempate determinístico;
- filtros: período, status, tipo, audience, participante e criador;
- busca textual em título e descrição.

### 5.2 Participantes

- `GET /api/events/{event_id}/participants/`
- `POST /api/events/{event_id}/participants/`
- `DELETE /api/events/{event_id}/participants/{user_id}/`

O POST aceita um ou mais IDs de usuários ativos e é idempotente para relações existentes.

### 5.3 Fotos vinculadas e thumbnail

- `GET /api/events/{event_id}/photos/`
- `POST /api/events/{event_id}/photos/`
- `DELETE /api/events/{event_id}/photos/{photo_id}/`
- `PUT /api/events/{event_id}/thumbnail/`

O POST aceita um ou mais IDs de fotos globais. O PUT recebe `photo_id` ou `null` para limpar a thumbnail.

### 5.4 Highlights

- `GET /api/events/{event_id}/highlights/`
- `POST /api/events/{event_id}/highlights/`
- `GET /api/events/{event_id}/highlights/{highlight_id}/`
- `PATCH /api/events/{event_id}/highlights/{highlight_id}/`
- `DELETE /api/events/{event_id}/highlights/{highlight_id}/`

O payload aceita texto e IDs de fotos já vinculadas ao evento.

### 5.5 Fotos globais e signed URLs

- `POST /api/media/photos/upload-urls/`
- `POST /api/media/photos/confirm/`
- `GET /api/media/photos/`
- `GET /api/media/photos/{photo_id}/`
- `PATCH /api/media/photos/{photo_id}/`
- `DELETE /api/media/photos/{photo_id}/`

`upload-urls` recebe entre 1 e 50 descritores com filename e MIME declarado e retorna uma signed URL PUT por item, chave, headers e expiração de cinco minutos. O frontend envia diretamente ao MinIO.

`confirm` recebe as chaves, datas e legendas. Antes de persistir, o backend executa HEAD em todos os objetos e valida lote emitido ao usuário, prefixo, existência, MIME e tamanho real. O lote inteiro é validado antes da criação dos registros, evitando confirmação parcial inconsistente.

A confirmação é a operação de criação das fotos; não existe um segundo POST genérico que aceite upload direto. A galeria retorna 20 itens por página, ordenados por `-taken_on` com desempate determinístico. Filtros: período, uploader, evento vinculado e busca na legenda.

### 5.6 Comentários

- `GET /api/comments/?target_type=events.event&target_id={uuid}`
- `POST /api/comments/`
- `GET /api/comments/{comment_id}/`
- `PATCH /api/comments/{comment_id}/`
- `DELETE /api/comments/{comment_id}/`

A criação recebe `target_type`, `target_id`, `parent_id` opcional e `body`. A listagem exige alvo e retorna 20 itens por página em forma plana, com `parent_id`. A ordenação deve ser determinística e permitir ao frontend reconstruir a árvore.

## 6. Permissões

- Leitura de eventos, fotos e comentários: qualquer usuário onboarded.
- Criar evento: qualquer usuário onboarded.
- Editar, cancelar, reativar, excluir e restaurar evento: criador ou staff.
- Gerenciar participantes: criador ou staff.
- Vincular fotos: criador, staff ou participante.
- Desvincular foto: quem criou o vínculo, criador ou staff.
- Criar foto global: qualquer usuário onboarded.
- Editar/excluir foto: uploader ou staff.
- Criar highlight: criador, staff ou participante.
- Editar/excluir highlight: autor; criador e staff moderam qualquer highlight.
- Criar comentário: qualquer usuário onboarded.
- Editar/excluir comentário: autor; somente staff modera comentários de terceiros.

## 7. Validação e consistência

- Serviços transacionais controlam alterações que cruzam tabelas.
- Restrições de banco impedem duplicidade e múltiplas thumbnails.
- O status é reconciliado em criação, leitura e escrita e por Celery Beat.
- Cancelar, reativar, restaurar, vincular e reconciliar devem ser idempotentes.
- Queries comuns excluem eventos com `deleted_at`.
- Eventos cancelados permanecem visíveis e editáveis.
- Fotos globais continuam visíveis quando eventos vinculados são excluídos.
- Comentários preservados de evento excluído ficam inacessíveis pela API comum.
- `select_related` e `prefetch_related` evitam N+1.

## 8. Erros

- `400`: payload, datas, endereço, arquivo, alvo ou relação inválida.
- `401`: autenticação ausente ou inválida.
- `403`: usuário autenticado sem permissão.
- `404`: recurso inexistente, excluído ou alvo indisponível.
- `409`: conflito de estado, duplicidade concorrente ou relação incompatível.
- `502/503`: falha temporária do MinIO.

Erros de validação serão associados aos campos. Em lotes, cada erro identificará o índice do item correspondente.

## 9. Django Admin

- Eventos com filtros por tipo, audience, status, data e exclusão.
- Busca por título e descrição.
- Participantes, audiences, localização, fotos e highlights acessíveis de forma administrável.
- Fotos com uploader, tipo, tamanho e data.
- Comentários com alvo, autor, pai e estado de exclusão.
- Staff autorizado pode visualizar e restaurar eventos excluídos.

## 10. Estratégia de testes

### Domínio e migrations

- Migration incremental preserva os dados do campo `public` ao criar audiences.
- Datas, endereço, audiences, participantes e thumbnail.
- Limites temporais de cada status e reconciliação.
- Cancelamento, reativação, soft delete e restauração.
- Relações de fotos e highlights.
- Allowlist, alvo e parentesco de comentários.

### API e permissões

- Usuário anônimo, onboarding pendente, usuário comum, participante, criador, uploader e staff.
- CRUD e ações de todos os recursos.
- Paginação, ordenação, busca e filtros.
- Ocultação correta após soft delete.
- Preservação da galeria e das threads.

### Storage e tarefas

- Lotes de 1 a 50 signed URLs e rejeição de 51.
- Extensão/MIME inválidos, chave alheia, objeto ausente e arquivo maior que 25 MB.
- Confirmação atômica do lote.
- Exclusão bem-sucedida e falhas transitórias do MinIO.
- Tarefa periódica idempotente, em lotes, sem N+1.

### Qualidade

- Testes de quantidade de queries nas listagens principais.
- `python manage.py check`, migrations check, `ruff`, `mypy` e suíte completa passam.

## 11. Critérios de aceite

1. Usuário onboarded cria, lista, consulta e filtra eventos.
2. Criador e staff administram ciclo de vida; demais usuários recebem `403`.
3. Criador é participante inicial e pode sair sem perder propriedade.
4. Evento aceita múltiplos audiences, um tipo e endereço brasileiro com coordenadas.
5. Status persistido permanece consistente com datas e cancelamento.
6. Evento excluído some da API comum e pode ser restaurado pelo criador ou staff.
7. Usuário gera até 50 signed URLs, envia ao MinIO e confirma fotos válidas.
8. Galeria global pagina, busca e filtra fotos independentes dos eventos.
9. A mesma foto pode ser vinculada a vários eventos.
10. Thumbnail é opcional e sempre corresponde a uma foto vinculada.
11. Highlights referenciam somente fotos do próprio evento.
12. Comentários genéricos aceitam Event, suportam threads ilimitadas e retornam lista plana.
13. Soft delete de comentário preserva respostas e placeholder.
14. Exclusão física de foto remove objeto e vínculos sem corromper eventos.
15. Admin, documentação básica e testes cobrem domínio, API, permissões, storage e tarefas.
