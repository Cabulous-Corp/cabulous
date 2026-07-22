# Cabulous Events API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar a API REST completa de eventos, fotos globais, highlights e comentários genéricos aprovada na spec da issue #7.

**Architecture:** Três apps Django separados (`events`, `media`, `comments`) expõem contratos REST via DRF e concentram regras cruzadas em serviços transacionais. Fotos são globais e reutilizáveis; eventos referenciam fotos por through model; comentários usam `ContentType + UUID` com allowlist explícita.

**Tech Stack:** Python 3.13, Django 6.0, Django REST Framework 3.16, django-filter 26.1, PostgreSQL 17, Celery 5.6, MinIO/S3, `django.test`, `APIClient`, Ruff e mypy.

## Global Constraints

- Executar comandos do backend a partir de `service/`.
- Seguir RED-GREEN-REFACTOR; nenhuma produção nova antes de um teste que falhe pelo motivo esperado.
- Usar migrations incrementais; nunca reescrever `events/migrations/0001_initial.py`.
- Todo endpoint exige autenticação e onboarding concluído.
- Paginação padrão: 20 itens.
- Foto: JPEG, PNG, WebP ou GIF; máximo real de 25 MB; lote de 1 a 50; signed URL de cinco minutos.
- Evento exige início, fim, um tipo e pelo menos um audience; localização é opcional, porém completa quando enviada.
- Highlight: máximo de 500 caracteres. Comentário: máximo de 5.000.
- Foto guarda `taken_on` como `DateField`, sem horário.
- Commits pequenos e convencionais; nunca incluir `service/docs/events-backend-spec.md`, que já estava untracked antes deste pipeline.

---

### Task 1: Infraestrutura compartilhada e entidade global Photo

**Files:**
- Modify: `service/pyproject.toml`
- Modify: `service/uv.lock`
- Modify: `service/cabulous/settings.py`
- Create: `service/common/pagination.py`
- Create: `service/media/__init__.py`
- Create: `service/media/apps.py`
- Create: `service/media/models.py`
- Create: `service/media/migrations/__init__.py`
- Create: `service/media/migrations/0001_initial.py`
- Create: `service/media/tests/__init__.py`
- Create: `service/media/tests/test_models.py`

**Interfaces:**
- Produces: `StandardPageNumberPagination`, `Photo`, `Photo.objects`, `Photo.event_links` reverse relation.
- Consumes: `common.models.abstracts.BaseModel`, `users.User`.

- [ ] **Step 1: Write the failing Photo model test**

```python
# media/tests/test_models.py
from datetime import date

from django.test import TestCase
from django.utils import timezone

from media.models import Photo
from users.models import User


class PhotoModelTests(TestCase):
    def test_photo_stores_global_metadata(self) -> None:
        user = User.objects.create_user(
            username="uploader",
            email="uploader@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )
        photo = Photo.objects.create(
            object_key=f"media/photos/{user.id}/photo.jpg",
            uploader=user,
            taken_on=date(2026, 7, 20),
            caption="Chegada",
            content_type="image/jpeg",
            size_bytes=1024,
        )

        self.assertEqual(photo.uploader, user)
        self.assertEqual(photo.taken_on, date(2026, 7, 20))
        self.assertEqual(photo.caption, "Chegada")
```

- [ ] **Step 2: Run RED and confirm the app/model is missing**

Run: `uv run python manage.py test media.tests.test_models.PhotoModelTests.test_photo_stores_global_metadata -v 2`
Expected: FAIL with import/app error for `media` or `Photo`.

- [ ] **Step 3: Add django-filter and scaffold the app**

Run: `uv add 'django-filter>=26.1'`

Add `"django_filters"` and `"media"` to `INSTALLED_APPS`. Create:

```python
# common/pagination.py
from rest_framework.pagination import PageNumberPagination


class StandardPageNumberPagination(PageNumberPagination):
    page_size = 20
```

```python
# media/apps.py
from django.apps import AppConfig


class MediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "media"
```

```python
# media/models.py
from django.conf import settings
from django.db import models

from common.models.abstracts import BaseModel


class Photo(BaseModel):
    object_key = models.CharField(max_length=1024, unique=True)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_photos",
    )
    taken_on = models.DateField()
    caption = models.TextField(blank=True, default="")
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()

    class Meta(BaseModel.Meta):
        ordering = ["-taken_on", "-created_at", "-id"]
        indexes = [
            models.Index(fields=["taken_on", "id"], name="media_photo_taken_idx"),
            models.Index(fields=["uploader", "taken_on"], name="media_photo_user_idx"),
        ]
```

- [ ] **Step 4: Generate and inspect the migration**

Run: `uv run python manage.py makemigrations media`
Expected: `media/migrations/0001_initial.py` creates `Photo` and both indexes.

- [ ] **Step 5: Run GREEN and the media app suite**

Run: `uv run python manage.py test media.tests.test_models -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add service/pyproject.toml service/uv.lock service/cabulous/settings.py service/common/pagination.py service/media
git commit -m "feat(media): add global photo domain"
```

---

### Task 2: Modelo completo de Event e migration incremental

**Files:**
- Modify: `service/events/models.py`
- Modify: `service/events/enums.py`
- Modify: `service/events/constants.py`
- Create: `service/events/migrations/0002_event_domain.py`
- Delete: `service/events/tests.py`
- Create: `service/events/tests/__init__.py`
- Create: `service/events/tests/factories.py`
- Create: `service/events/tests/test_models.py`

**Interfaces:**
- Produces: `Event`, `EventAudience`, `EventParticipant`, `EventLocation`, `EventPhoto`, `Highlight`, `HighlightPhoto`, `EventStatus`, `Audience`.
- Consumes: `media.Photo`, `users.User`, common base/soft-delete abstractions.

- [ ] **Step 1: Write failing domain tests for dates, audiences and thumbnail constraints**

```python
# events/tests/test_models.py
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from events.enums import Audience, EventStatus, EventType
from events.models import Event, EventAudience
from users.models import User


class EventModelTests(TestCase):
    def setUp(self) -> None:
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_event_rejects_end_before_start(self) -> None:
        start = timezone.now()
        event = Event(
            title="Evento",
            description="",
            start_at=start,
            end_at=start - timedelta(minutes=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )

        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_event_audience_is_unique_per_event(self) -> None:
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Evento",
            start_at=start,
            end_at=start + timedelta(hours=4),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        EventAudience.objects.create(event=event, audience=Audience.ILUMINADOS)

        with self.assertRaises(IntegrityError), transaction.atomic():
            EventAudience.objects.create(event=event, audience=Audience.ILUMINADOS)
```

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test events.tests.test_models -v 2`
Expected: FAIL because the new enums, fields and models do not exist.

- [ ] **Step 3: Implement enums and models minimally**

Add enums:

```python
class Audience(models.TextChoices):
    ILUMINADOS = "ILUMINADOS", "Iluminados"
    VOYEURS = "VOYEURS", "Voyeurs"
    ELETRONICOS = "ELETRONICOS", "Eletrônicos"
    OTHERS = "OTHERS", "Outros"


class EventStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Agendado"
    IN_PROGRESS = "IN_PROGRESS", "Em andamento"
    COMPLETED = "COMPLETED", "Concluído"
    CANCELLED = "CANCELLED", "Cancelado"
```

Update `Event` to inherit `AbstractSoftDeleteModel, BaseModel`; remove the direct `ImageField thumbnail`; add required `creator`, `status`, `cancelled_at`, required `end_at`, active/all managers and deterministic ordering. Add the six related models with these database constraints:

```python
models.UniqueConstraint(fields=["event", "audience"], name="events_audience_unique")
models.UniqueConstraint(fields=["event", "user"], name="events_participant_unique")
models.UniqueConstraint(fields=["event", "photo"], name="events_photo_unique")
models.UniqueConstraint(
    fields=["event"],
    condition=models.Q(is_thumbnail=True),
    name="events_one_thumbnail",
)
models.CheckConstraint(
    condition=models.Q(end_at__gte=models.F("start_at")),
    name="events_end_gte_start",
)
```

`EventLocation` uses `DecimalField(max_digits=9, decimal_places=6)` for latitude and `DecimalField(max_digits=10, decimal_places=6)` for longitude. `Highlight.text` uses `CharField(max_length=500)`.

- [ ] **Step 4: Write the migration with data preservation**

Create `0002_event_domain.py` with this operation order:

1. Add nullable `creator`, nullable `status`, `cancelled_at`, `deleted_at`.
2. Create all related tables.
3. Run Python migration that creates one `EventAudience` from each old `public`, chooses the first superuser or active user as creator, computes status from dates, and raises `RuntimeError` if events exist without any user.
4. Alter `creator`, `status` and `end_at` to non-null.
5. Remove old `public` and `thumbnail` columns.
6. Add indexes and constraints.

Reverse migration restores `public` from the first audience ordered by creation and leaves removed thumbnail null.

- [ ] **Step 5: Add tests for migration behavior and full model graph**

Add tests covering optional location, complete address validation, creator participant independence, multiple audiences, photo reuse between events, one thumbnail, highlight photo relation and active/all managers.

Run: `uv run python manage.py test events.tests.test_models -v 2`
Expected: PASS.

- [ ] **Step 6: Verify migrations**

Run: `uv run python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

- [ ] **Step 7: Commit**

```bash
git add service/events
git commit -m "feat(events): model event domain and relations"
```

---

### Task 3: Ciclo de vida e reconciliação de status

**Files:**
- Create: `service/events/services/__init__.py`
- Create: `service/events/services/lifecycle.py`
- Create: `service/events/tasks.py`
- Modify: `service/cabulous/settings.py`
- Create: `service/events/tests/test_lifecycle.py`

**Interfaces:**
- Produces: `calculate_event_status`, `reconcile_event_status`, `cancel_event`, `reactivate_event`, `restore_event`, `reconcile_event_statuses` Celery task.
- Consumes: `Event`, `EventStatus`.

- [ ] **Step 1: Write boundary tests before implementation**

```python
# events/tests/test_lifecycle.py
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from events.enums import EventStatus
from events.services.lifecycle import calculate_event_status


class CalculateEventStatusTests(TestCase):
    def test_status_is_scheduled_before_start(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now + timedelta(seconds=1),
            end_at=now + timedelta(hours=1),
            cancelled_at=None,
            now=now,
        )
        self.assertEqual(status, EventStatus.SCHEDULED)

    def test_status_is_in_progress_at_exact_end(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now - timedelta(hours=1),
            end_at=now,
            cancelled_at=None,
            now=now,
        )
        self.assertEqual(status, EventStatus.IN_PROGRESS)

    def test_cancelled_overrides_dates(self) -> None:
        now = timezone.now()
        status = calculate_event_status(
            start_at=now - timedelta(days=2),
            end_at=now - timedelta(days=1),
            cancelled_at=now,
            now=now,
        )
        self.assertEqual(status, EventStatus.CANCELLED)
```

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test events.tests.test_lifecycle.CalculateEventStatusTests -v 2`
Expected: FAIL because `events.services.lifecycle` is missing.

- [ ] **Step 3: Implement lifecycle services**

```python
# events/services/lifecycle.py
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from events.enums import EventStatus
from events.models import Event


def calculate_event_status(*, start_at: datetime, end_at: datetime, cancelled_at: datetime | None, now: datetime) -> EventStatus:
    if cancelled_at is not None:
        return EventStatus.CANCELLED
    if now < start_at:
        return EventStatus.SCHEDULED
    if now <= end_at:
        return EventStatus.IN_PROGRESS
    return EventStatus.COMPLETED


@transaction.atomic
def reconcile_event_status(*, event: Event, now: datetime | None = None) -> Event:
    effective_now = now or timezone.now()
    expected = calculate_event_status(
        start_at=event.start_at,
        end_at=event.end_at,
        cancelled_at=event.cancelled_at,
        now=effective_now,
    )
    if event.status != expected:
        event.status = expected
        event.save(update_fields=["status", "updated_at"])
    return event
```

Implement cancellation/reactivation/restoration as idempotent atomic operations; restoration clears `deleted_at` and reconciles status.

- [ ] **Step 4: Add Celery task and one-minute schedule**

The task iterates active event IDs in chunks of 500, locks rows in bounded transactions and returns the updated count. Add:

```python
"events_reconcile_statuses_every_minute": {
    "task": "events.tasks.reconcile_event_statuses",
    "schedule": crontab(minute="*"),
},
```

- [ ] **Step 5: Test idempotency and task batching**

Run: `uv run python manage.py test events.tests.test_lifecycle -v 2`
Expected: PASS for boundaries, cancel twice, reactivate twice, restore twice and task repeated twice.

- [ ] **Step 6: Commit**

```bash
git add service/events/services service/events/tasks.py service/events/tests/test_lifecycle.py service/cabulous/settings.py
git commit -m "feat(events): add event lifecycle reconciliation"
```

---

### Task 4: Upload assinado, confirmação e CRUD de fotos

**Files:**
- Create: `service/media/services/__init__.py`
- Create: `service/media/services/upload_signing.py`
- Create: `service/media/services/deletion.py`
- Create: `service/media/serializers.py`
- Create: `service/media/permissions.py`
- Create: `service/media/filters.py`
- Create: `service/media/views.py`
- Create: `service/media/urls.py`
- Modify: `service/cabulous/urls.py`
- Create: `service/media/tests/test_uploads.py`
- Create: `service/media/tests/test_api.py`

**Interfaces:**
- Produces: upload URL endpoint, atomic confirm endpoint, paginated global Photo API, `hard_delete_photo`.
- Consumes: `Photo`, MinIO settings/default storage, onboarding guard, standard pagination.

- [ ] **Step 1: Write failing upload validation tests**

Test these behaviors separately: 50 accepted, 51 rejected, GIF accepted, non-image rejected, declared size above 25 MB rejected, foreign key prefix rejected, HEAD MIME mismatch rejected, HEAD size overflow rejected and one invalid object prevents the whole confirm batch.

```python
@patch("media.services.upload_signing._build_s3_client")
def test_generate_rejects_more_than_fifty_files(self, client_builder: Mock) -> None:
    payload = [{"filename": f"{index}.jpg", "content_type": "image/jpeg"} for index in range(51)]
    response = self.client.post("/api/media/photos/upload-urls/", {"files": payload}, format="json")
    self.assertEqual(response.status_code, 400)
    client_builder.assert_not_called()
```

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test media.tests.test_uploads -v 2`
Expected: FAIL with missing routes/services.

- [ ] **Step 3: Implement signed URL service**

Define constants exactly:

```python
SIGNED_URL_EXPIRES_IN_SECONDS = 300
MAX_UPLOAD_BATCH = 50
MAX_PHOTO_SIZE_BYTES = 25 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/gif": {".gif"},
}
```

Generate keys as `media/photos/{user.id}/{uuid4().hex}{suffix}`. Reuse the internal/public S3 client pattern from `users/services/upload_signing.py`, but do not couple photo services to the users app service.

- [ ] **Step 4: Implement serializers and views for upload and confirmation**

`PhotoUploadUrlsSerializer` validates 1..50 items. `PhotoConfirmSerializer` validates the entire list, calls HEAD for every key, then uses one `transaction.atomic()` and `bulk_create`. The response preserves request order.

- [ ] **Step 5: Write failing CRUD/permission/filter tests**

Cover anonymous 401, pending onboarding 403 payload, onboarded list/create only through confirm, uploader PATCH/DELETE, non-owner 403, staff override, pagination 20, ordering by date and filters for `taken_from`, `taken_until`, `uploader`, `event` and `search` caption.

- [ ] **Step 6: Implement Photo ViewSet and hard deletion**

`PhotoViewSet` exposes list/retrieve/partial_update/destroy; it does not expose generic create. `perform_destroy` calls:

```python
def hard_delete_photo(*, photo: Photo) -> None:
    storage = default_storage
    key = photo.object_key
    storage.delete(key)
    photo.delete()
```

Translate storage failures to `ServiceUnavailable` without changing the database.

- [ ] **Step 7: Run media tests**

Run: `uv run python manage.py test media.tests -v 2`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add service/media service/cabulous/urls.py
git commit -m "feat(media): add signed photo upload API"
```

---

### Task 5: CRUD, filtros e autorização de eventos

**Files:**
- Create: `service/events/services/events.py`
- Create: `service/events/serializers.py`
- Create: `service/events/permissions.py`
- Create: `service/events/filters.py`
- Modify: `service/events/views.py`
- Create: `service/events/urls.py`
- Modify: `service/cabulous/urls.py`
- Create: `service/events/tests/test_api.py`

**Interfaces:**
- Produces: `/api/events/` CRUD, `/options/`, `/cancel/`, `/reactivate/`, `/restore/`.
- Consumes: event models, lifecycle services, standard pagination, django-filter.

- [ ] **Step 1: Write failing create/list tests**

```python
def test_onboarded_user_creates_event_and_becomes_participant(self) -> None:
    self.client.force_authenticate(self.user)
    response = self.client.post(
        "/api/events/",
        {
            "title": "Cabulous Day",
            "description": "Memórias",
            "start_at": "2026-08-01T18:00:00-03:00",
            "end_at": "2026-08-02T02:00:00-03:00",
            "type": "CABULOUS",
            "audiences": ["ILUMINADOS", "VOYEURS"],
        },
        format="json",
    )
    self.assertEqual(response.status_code, 201)
    event = Event.objects.get(id=response.data["id"])
    self.assertEqual(event.creator, self.user)
    self.assertTrue(event.participants.filter(user=self.user).exists())
```

Add separate RED tests for empty audiences, incomplete location, end before start, creator/staff edit, other user 403, cancel/reactivate visibility, delete/restore and anonymous/pending onboarding.

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test events.tests.test_api -v 2`
Expected: FAIL because serializers/routes are missing.

- [ ] **Step 3: Implement transactional create/update service**

`create_event` creates Event, at least one EventAudience, optional complete EventLocation and creator participant in one transaction. `update_event` replaces audiences/location only when those keys are present and calls `reconcile_event_status` after date changes.

- [ ] **Step 4: Implement serializers, filterset and ViewSet**

`EventFilter` declares `starts_from`, `starts_until`, `status`, `type`, `audience`, `participant`, `creator`. `EventViewSet` uses `SearchFilter` on title/description and `OrderingFilter` allowlist. Queryset uses `distinct()` for M2M filters and prefetches relations.

The serializer exposes labels/colors read-only and returns thumbnail through the active `EventPhoto(is_thumbnail=True)` relation.

- [ ] **Step 5: Implement options and lifecycle actions**

`options` returns enum value/label/color. Actions call services and use the same creator/staff permission. `restore` resolves against `Event.all_objects.deleted()` instead of the active queryset.

- [ ] **Step 6: Verify filtering and query count**

Add 25 events and assert 20 results on page 1. Use `assertNumQueries` around a fixed list size to ensure participants/audiences/location/thumbnail do not produce N+1.

Run: `uv run python manage.py test events.tests.test_api -v 2`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add service/events service/cabulous/urls.py
git commit -m "feat(events): add event CRUD API"
```

---

### Task 6: Participantes, vínculos de fotos e thumbnail

**Files:**
- Create: `service/events/services/relations.py`
- Modify: `service/events/serializers.py`
- Modify: `service/events/views.py`
- Modify: `service/events/urls.py`
- Create: `service/events/tests/test_relations.py`

**Interfaces:**
- Produces: participant endpoints, photo link endpoints, thumbnail endpoint.
- Consumes: `EventParticipant`, `EventPhoto`, `Photo`, creator/staff/participant permissions.

- [ ] **Step 1: Write failing participant tests**

Cover creator/staff batch add, duplicate add idempotency, inactive/deleted user rejection, non-owner 403, creator removal without ownership loss and pagination.

- [ ] **Step 2: Run participant RED**

Run: `uv run python manage.py test events.tests.test_relations.ParticipantApiTests -v 2`
Expected: FAIL with missing actions.

- [ ] **Step 3: Implement participant services/actions**

Use `bulk_create(ignore_conflicts=True)` after validating every user ID. Return canonical persisted rows in request order. Deletion removes only the association.

- [ ] **Step 4: Write failing photo relation tests**

Cover creator/staff/participant link, outsider 403, participant unlink only when `linked_by` is self, creator/staff unlink any, same Photo on two events, set/replace/clear thumbnail, reject unlinked thumbnail, and deleted Photo cascading thumbnail to null representation.

- [ ] **Step 5: Run photo relation RED**

Run: `uv run python manage.py test events.tests.test_relations.EventPhotoApiTests -v 2`
Expected: FAIL with missing services/actions.

- [ ] **Step 6: Implement relation services atomically**

```python
@transaction.atomic
def set_thumbnail(*, event: Event, photo: Photo | None) -> EventPhoto | None:
    EventPhoto.objects.filter(event=event, is_thumbnail=True).update(is_thumbnail=False)
    if photo is None:
        return None
    relation = EventPhoto.objects.filter(event=event, photo=photo).first()
    if relation is None:
        raise ValidationError({"photo_id": "Photo is not linked to this event."})
    relation.is_thumbnail = True
    relation.save(update_fields=["is_thumbnail"])
    return relation
```

Catch `IntegrityError` from concurrent thumbnail updates and retry once inside a new atomic block or return 409 after re-reading the winning state.

- [ ] **Step 7: Run relation suite**

Run: `uv run python manage.py test events.tests.test_relations -v 2`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add service/events/services/relations.py service/events/serializers.py service/events/views.py service/events/urls.py service/events/tests/test_relations.py
git commit -m "feat(events): manage participants and event photos"
```

---

### Task 7: Highlights com fotos vinculadas

**Files:**
- Create: `service/events/services/highlights.py`
- Modify: `service/events/serializers.py`
- Modify: `service/events/views.py`
- Modify: `service/events/urls.py`
- Create: `service/events/tests/test_highlights.py`

**Interfaces:**
- Produces: nested highlight CRUD and moderation.
- Consumes: `Highlight`, `HighlightPhoto`, `EventPhoto`.

- [ ] **Step 1: Write failing highlight tests**

Test creator/staff/participant create, outsider 403, 500 accepted, 501 rejected, unlinked photo rejected, linked photos accepted, author edit/delete, creator/staff moderation, unrelated participant 403 and physical delete preserving Photo.

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test events.tests.test_highlights -v 2`
Expected: FAIL because highlight API is absent.

- [ ] **Step 3: Implement highlight service**

Validate all photo IDs before creating anything. In one transaction create/update Highlight and replace HighlightPhoto rows. Never delete Photo objects.

- [ ] **Step 4: Implement nested serializers/views/routes**

The queryset is constrained by `event_id` from the URL so a highlight UUID from another event returns 404. Serializer returns photos in stable order.

- [ ] **Step 5: Run GREEN**

Run: `uv run python manage.py test events.tests.test_highlights -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add service/events/services/highlights.py service/events/serializers.py service/events/views.py service/events/urls.py service/events/tests/test_highlights.py
git commit -m "feat(events): add event highlights"
```

---

### Task 8: Domínio genérico de comentários

**Files:**
- Create: `service/comments/__init__.py`
- Create: `service/comments/apps.py`
- Create: `service/comments/models.py`
- Create: `service/comments/targets.py`
- Create: `service/comments/services.py`
- Create: `service/comments/migrations/__init__.py`
- Create: `service/comments/migrations/0001_initial.py`
- Create: `service/comments/tests/__init__.py`
- Create: `service/comments/tests/test_models.py`
- Modify: `service/cabulous/settings.py`

**Interfaces:**
- Produces: `Comment`, `resolve_target`, `create_comment`, `soft_delete_comment`.
- Consumes: `ContentType`, `Event`, `User`.

- [ ] **Step 1: Write failing generic target/thread tests**

```python
class CommentDomainTests(TestCase):
    def test_child_must_share_parent_target(self) -> None:
        parent = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event_a.id,
            body="Pai",
            parent=None,
        )
        with self.assertRaises(ValidationError):
            create_comment(
                author=self.user,
                target_type="events.event",
                target_id=self.event_b.id,
                body="Filho",
                parent=parent,
            )
```

Also test unknown type, deleted event, arbitrary deep chain, 5,000 accepted, 5,001 rejected, immutable parent and soft-delete placeholder behavior.

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test comments.tests.test_models -v 2`
Expected: FAIL because comments app is missing.

- [ ] **Step 3: Implement app, model and target registry**

```python
# comments/targets.py
from django.db.models import Model

from events.models import Event

ALLOWED_TARGETS: dict[str, type[Model]] = {"events.event": Event}


def resolve_target_model(target_type: str) -> type[Model]:
    model = ALLOWED_TARGETS.get(target_type)
    if model is None:
        raise ValidationError({"target_type": "Unsupported comment target type."})
    return model
```

`Comment` includes `GenericForeignKey`, UUID target ID, self parent, body max length 5,000, `deleted_at`, deterministic ordering and composite target index.

- [ ] **Step 4: Implement services and migration**

`create_comment` resolves only active Events, validates parent target equality and saves atomically. `soft_delete_comment` clears body or ensures serializers never expose it and leaves parent/children intact.

- [ ] **Step 5: Run GREEN**

Run: `uv run python manage.py test comments.tests.test_models -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add service/comments service/cabulous/settings.py
git commit -m "feat(comments): add typed generic comment domain"
```

---

### Task 9: API plana e paginada de comentários

**Files:**
- Create: `service/comments/serializers.py`
- Create: `service/comments/permissions.py`
- Create: `service/comments/views.py`
- Create: `service/comments/urls.py`
- Create: `service/comments/admin.py`
- Create: `service/comments/tests/test_api.py`
- Modify: `service/cabulous/urls.py`

**Interfaces:**
- Produces: `/api/comments/` list/create and detail/update/delete.
- Consumes: comment services, target registry, standard pagination.

- [ ] **Step 1: Write failing API and permission tests**

Cover required `target_type` and `target_id`, flat `parent_id`, 20 per page, deterministic chronological order, arbitrary depth without recursive serialization, author edit/delete, non-author 403, staff moderation, event creator without staff cannot moderate, anonymous 401, onboarding pending 403 and deleted target 404.

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test comments.tests.test_api -v 2`
Expected: FAIL with missing routes.

- [ ] **Step 3: Implement serializers and permissions**

Create serializer accepts target strings and `parent_id`; read serializer emits `is_deleted`, `parent_id`, author summary and body `null` for deleted comments. `parent` and target fields are immutable on PATCH.

- [ ] **Step 4: Implement ViewSet and routes**

List requires both target query params, resolves allowlist before filtering, excludes comments whose Event target is deleted, paginates 20 and orders by `created_at, id`. Destroy calls soft delete and returns 204.

- [ ] **Step 5: Run GREEN**

Run: `uv run python manage.py test comments.tests.test_api -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add service/comments service/cabulous/urls.py
git commit -m "feat(comments): expose threaded comments API"
```

---

### Task 10: Django Admin, performance, documentação e quality gates

**Files:**
- Modify: `service/events/admin.py`
- Create: `service/media/admin.py`
- Modify: `service/comments/admin.py`
- Modify: `service/README.md`
- Modify: `service/events/tests/test_api.py`
- Modify: `service/media/tests/test_api.py`
- Modify: `service/comments/tests/test_api.py`
- Create: `service/events/tests/test_admin.py`
- Create: `service/media/tests/test_admin.py`
- Create: `service/comments/tests/test_admin.py`

**Interfaces:**
- Produces: operable Admin, documented API, verified query budgets and final green suite.
- Consumes: every model/view/service from Tasks 1–9.

- [ ] **Step 1: Write failing Admin tests**

Verify each model is registered, event list exposes status/deleted filters, staff can restore a deleted event through the approved admin action, and Photo/Comment admin display uploader/target/deleted state.

- [ ] **Step 2: Run RED**

Run: `uv run python manage.py test events.tests.test_admin media.tests.test_admin comments.tests.test_admin -v 2`
Expected: FAIL because registrations/actions are absent.

- [ ] **Step 3: Implement focused Admin classes**

Use `list_display`, `list_filter`, `search_fields`, `autocomplete_fields` and read-only metadata. Restoration action calls `restore_event`; do not update `deleted_at` directly.

- [ ] **Step 4: Add query-budget regression tests**

Seed fixed graphs and use `assertNumQueries` for one event page, one photo page and one comment page. Capture the initial optimized count in the assertion and document why each query exists next to the assertion.

- [ ] **Step 5: Document routes and upload flow**

Add a `Cabulous Events API` section to `service/README.md` listing route prefixes, signed URL → PUT → confirm flow, size/type limits, pagination and the three app responsibilities. Link the approved design spec.

- [ ] **Step 6: Run Django checks and migration checks**

Run: `uv run python manage.py check`
Expected: no issues.

Run: `uv run python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

- [ ] **Step 7: Run focused and full test suites**

Run: `uv run python manage.py test media events comments -v 2`
Expected: PASS.

Run: `uv run python manage.py test`
Expected: entire Django suite PASS.

- [ ] **Step 8: Run static quality gates**

Run: `uv run ruff check .`
Expected: PASS.

Run: `uv run ruff format --check .`
Expected: PASS.

- [ ] **Step 9: Inspect final diff and ensure old untracked draft is untouched**

Run: `git status --short && git diff --check && git diff --stat develop...HEAD`
Expected: no whitespace errors; `service/docs/events-backend-spec.md` remains untracked and absent from staged changes.

- [ ] **Step 10: Commit**

```bash
git add service/events/admin.py service/events/tests service/media/admin.py service/media/tests service/comments/admin.py service/comments/tests service/README.md
git commit -m "docs(events): finalize admin and API verification"
```

---

## Plan Self-Review Record

- Spec coverage: all 15 acceptance criteria map to Tasks 1–10.
- TDD order: every production slice starts with one or more focused failing tests and an explicit RED command.
- Type consistency: `taken_on`, `EventStatus`, `Audience`, `EventPhoto.is_thumbnail`, generic `target_object_id` UUID and service names match the architecture.
- Migration safety: existing `0001_initial.py` remains untouched and the old singular audience is preserved before column removal.
- External consistency: MinIO confirmation and deletion failure paths have explicit tests.
- Scope control: frontend, notifications, recurrence, EXIF and user tagging remain excluded.
