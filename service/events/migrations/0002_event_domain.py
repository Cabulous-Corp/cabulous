import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _compute_status(start_at: object, end_at: object) -> str:
    from django.utils import timezone

    now = timezone.now()
    if end_at and now > end_at:
        return "COMPLETED"
    if start_at <= now <= (end_at or now):
        return "IN_PROGRESS"
    return "SCHEDULED"


def _find_creator(apps: object, schema_editor: object) -> object:
    User = apps.get_model(settings.AUTH_USER_MODEL)
    user = User.objects.filter(is_superuser=True).order_by("date_joined").first()
    if user is None:
        user = User.objects.filter(is_active=True).order_by("date_joined").first()
    return user


def forwards(apps: object, schema_editor: object) -> None:
    Event = apps.get_model("events", "Event")
    EventAudience = apps.get_model("events", "EventAudience")
    User = apps.get_model(settings.AUTH_USER_MODEL)

    creator = _find_creator(apps, schema_editor)
    if creator is None:
        if Event.objects.exists():
            raise RuntimeError("Cannot backfill: events exist but no active users found.")
        return

    for event in Event.objects.all():
        EventAudience.objects.create(event=event, audience=event.public)
        event.creator_id = creator.id
        event.status = _compute_status(event.start_at, event.end_at)
        event.save(update_fields=["creator_id", "status"])


def reverse(apps: object, schema_editor: object) -> None:
    Event = apps.get_model("events", "Event")
    EventAudience = apps.get_model("events", "EventAudience")
    for event in Event.objects.all():
        first_aud = EventAudience.objects.filter(event=event).order_by("created_at").first()
        if first_aud:
            event.public = first_aud.audience
            event.save(update_fields=["public"])


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("events", "0001_initial"),
        ("media", "0001_initial"),
    ]

    operations = [
        # Step 1: Add nullable new fields
        migrations.AddField(
            model_name="event",
            name="creator",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_events",
                verbose_name="Criador",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="status",
            field=models.CharField(
                choices=[
                    ("SCHEDULED", "Agendado"),
                    ("IN_PROGRESS", "Em andamento"),
                    ("COMPLETED", "ConcluÃ­do"),
                    ("CANCELLED", "Cancelado"),
                ],
                max_length=20,
                null=True,
                verbose_name="Status",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="cancelled_at",
            field=models.DateTimeField(null=True, blank=True, verbose_name="Cancelado em"),
        ),
        migrations.AddField(
            model_name="event",
            name="deleted_at",
            field=models.DateTimeField(null=True, blank=True, verbose_name="ExcluÃ­do em"),
        ),
        # Step 2: Create related tables
        migrations.CreateModel(
            name="EventAudience",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "audience",
                    models.CharField(
                        choices=[
                            ("ILUMINADOS", "Iluminados"),
                            ("VOYEURS", "Voyeurs"),
                            ("ELETRONICOS", "EletrÃ´nicos"),
                            ("OTHERS", "Outros"),
                        ],
                        max_length=30,
                        verbose_name="PÃºblico-alvo",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audiences",
                        to="events.event",
                    ),
                ),
            ],
            options={
                "verbose_name": "PÃºblico do evento",
                "verbose_name_plural": "PÃºblicos do evento",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="EventParticipant",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        to="events.event",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_participations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Participante",
                "verbose_name_plural": "Participantes",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="EventLocation",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="Nome do local"),
                ),
                ("address", models.TextField(verbose_name="EndereÃ§o")),
                ("latitude", models.DecimalField(max_digits=9, decimal_places=6)),
                ("longitude", models.DecimalField(max_digits=10, decimal_places=6)),
                (
                    "event",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location",
                        to="events.event",
                    ),
                ),
            ],
            options={
                "verbose_name": "Local do evento",
                "verbose_name_plural": "Locais do evento",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="EventPhoto",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "is_thumbnail",
                    models.BooleanField(default=False, verbose_name="Ã‰ thumbnail"),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="photos",
                        to="events.event",
                    ),
                ),
                (
                    "photo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_photos",
                        to="media.photo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Foto do evento",
                "verbose_name_plural": "Fotos do evento",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Highlight",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("text", models.CharField(max_length=500, verbose_name="Texto")),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="highlights",
                        to="events.event",
                    ),
                ),
            ],
            options={
                "verbose_name": "Destaque",
                "verbose_name_plural": "Destaques",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="HighlightPhoto",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "highlight",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="photos",
                        to="events.highlight",
                    ),
                ),
                (
                    "photo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="highlight_photos",
                        to="media.photo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Foto do destaque",
                "verbose_name_plural": "Fotos do destaque",
                "abstract": False,
            },
        ),
        # Step 3: Data migration
        migrations.RunPython(forwards, reverse),
        # Step 4: Make fields non-nullable
        migrations.AlterField(
            model_name="event",
            name="creator",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_events",
                verbose_name="Criador",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="status",
            field=models.CharField(
                choices=[
                    ("SCHEDULED", "Agendado"),
                    ("IN_PROGRESS", "Em andamento"),
                    ("COMPLETED", "ConcluÃ­do"),
                    ("CANCELLED", "Cancelado"),
                ],
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="end_at",
            field=models.DateTimeField(verbose_name="Fim do evento"),
        ),
        # Step 5: Remove old indexes (SQLite requires this before column drop)
        migrations.RemoveIndex(
            model_name="event",
            name="events_even_type_53534a_idx",
        ),
        migrations.RemoveIndex(
            model_name="event",
            name="events_even_public_5bbabb_idx",
        ),
        # Step 6: Remove old columns
        migrations.RemoveField(
            model_name="event",
            name="public",
        ),
        migrations.RemoveField(
            model_name="event",
            name="thumbnail",
        ),
        # Step 7: New indexes and constraints
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["type", "start_at"], name="events_type_start_idx"),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.CheckConstraint(
                condition=models.Q(end_at__gte=models.F("start_at")),
                name="events_end_gte_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="eventaudience",
            constraint=models.UniqueConstraint(
                fields=["event", "audience"], name="events_audience_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="eventparticipant",
            constraint=models.UniqueConstraint(
                fields=["event", "user"], name="events_participant_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="eventphoto",
            constraint=models.UniqueConstraint(
                fields=["event", "photo"], name="events_photo_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="eventphoto",
            constraint=models.UniqueConstraint(
                fields=["event"],
                condition=models.Q(is_thumbnail=True),
                name="events_one_thumbnail",
            ),
        ),
    ]
