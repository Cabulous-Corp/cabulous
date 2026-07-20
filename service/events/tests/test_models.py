from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from events.enums import Audience, EventStatus, EventType
from events.models import (
    Event,
    EventAudience,
    EventLocation,
    EventParticipant,
    EventPhoto,
    Highlight,
    HighlightPhoto,
)
from media.models import Photo
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

    def test_active_manager_excludes_soft_deleted_events(self) -> None:
        now = timezone.now()
        active = Event.objects.create(
            title="Ativo",
            start_at=now,
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        inactive = Event.objects.create(
            title="Inativo",
            start_at=now,
            end_at=now + timedelta(hours=1),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        inactive.soft_delete()

        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Event.objects.first().id, active.id)
        self.assertEqual(Event.all_objects.count(), 2)

    def test_all_objects_manager_returns_soft_deleted(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        event.soft_delete()

        self.assertIn(event, Event.all_objects.deleted())
        self.assertNotIn(event, Event.all_objects.active())

    def test_status_is_persisted(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=2),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.COMPLETED,
        )
        self.assertEqual(event.status, EventStatus.COMPLETED)
        self.assertEqual(EventStatus(event.status), EventStatus.COMPLETED)

    def test_event_participant_unique_per_event_and_user(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        user = User.objects.create_user(
            username="participant",
            email="participant@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )
        EventParticipant.objects.create(event=event, user=user)

        with self.assertRaises(IntegrityError), transaction.atomic():
            EventParticipant.objects.create(event=event, user=user)

    def test_event_location_is_one_to_one(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        EventLocation.objects.create(
            event=event,
            name="Casa",
            street="Rua A",
            number="123",
            neighborhood="Bairro",
            city="Cidade",
            state="SP",
            postal_code="01001000",
            latitude="23.550000",
            longitude="-46.633300",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            EventLocation.objects.create(
                event=event,
                name="Sobrado",
                street="Rua B",
                number="5",
                neighborhood="Outro",
                city="Outra",
                state="RJ",
                postal_code="20001000",
                latitude="-22.906847",
                longitude="-43.172900",
            )

    def test_event_photo_is_unique_per_event_and_photo(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        photo = Photo.objects.create(
            object_key="media/photos/photo-1.jpg",
            uploader=self.creator,
            taken_on=timezone.now().date(),
            caption="Foto",
            content_type="image/jpeg",
            size_bytes=1024,
        )
        EventPhoto.objects.create(event=event, photo=photo, linked_by=self.creator)

        with self.assertRaises(IntegrityError), transaction.atomic():
            EventPhoto.objects.create(event=event, photo=photo, linked_by=self.creator)

    def test_only_one_thumbnail_per_event(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        photo_one = Photo.objects.create(
            object_key="media/photos/photo-a.jpg",
            uploader=self.creator,
            taken_on=timezone.now().date(),
            caption="A",
            content_type="image/jpeg",
            size_bytes=1024,
        )
        photo_two = Photo.objects.create(
            object_key="media/photos/photo-b.jpg",
            uploader=self.creator,
            taken_on=timezone.now().date(),
            caption="B",
            content_type="image/jpeg",
            size_bytes=2048,
        )
        EventPhoto.objects.create(event=event, photo=photo_one, linked_by=self.creator, is_thumbnail=True)

        with self.assertRaises(IntegrityError), transaction.atomic():
            EventPhoto.objects.create(
                event=event, photo=photo_two, linked_by=self.creator, is_thumbnail=True
            )

    def test_highlight_photo_is_unique_per_highlight_and_photo(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        highlight = Highlight.objects.create(
            event=event,
            author=self.creator,
            text="Momento especial",
        )
        photo = Photo.objects.create(
            object_key="media/photos/photo-h.jpg",
            uploader=self.creator,
            taken_on=timezone.now().date(),
            caption="H",
            content_type="image/jpeg",
            size_bytes=1024,
        )
        event_photo = EventPhoto.objects.create(event=event, photo=photo, linked_by=self.creator)
        HighlightPhoto.objects.create(highlight=highlight, photo=photo)
        HighlightPhoto.objects.create(highlight=highlight, photo=event_photo)

        with self.assertRaises(IntegrityError), transaction.atomic():
            HighlightPhoto.objects.create(highlight=highlight, photo=photo)

    def test_multiple_audiences_are_allowed_for_one_event(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        EventAudience.objects.create(event=event, audience=Audience.ILUMINADOS)
        EventAudience.objects.create(event=event, audience=Audience.VOYEURS)
        self.assertEqual(event.audiences.count(), 2)
