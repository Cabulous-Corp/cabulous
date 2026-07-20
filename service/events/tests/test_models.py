from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock, patch

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
    event_thumbnail_upload_to,
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

    def event_location(self, **overrides: Any) -> EventLocation:
        now = timezone.now()
        event = Event.objects.create(
            title="Evento com local",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        values = {
            "event": event,
            "name": "Casa",
            "street": "Rua A",
            "number": "123",
            "neighborhood": "Bairro",
            "city": "Cidade",
            "state": "SP",
            "postal_code": "01001000",
            "country": "BR",
            "latitude": "23.550000",
            "longitude": "-46.633300",
        }
        values.update(overrides)
        return EventLocation(**values)

    @patch("events.models.uuid.uuid4")
    def test_legacy_thumbnail_upload_path_is_backwards_compatible(self, uuid4: MagicMock) -> None:
        uuid4.return_value.hex = "abc123"

        path = event_thumbnail_upload_to(Event(title="Festa Cabulosa"), "PHOTO.JPG")

        self.assertEqual(path, "events/thumbnails/festa-cabulosa-abc123.jpg")

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
        first_event = Event.objects.first()
        self.assertIsNotNone(first_event)
        assert first_event is not None
        self.assertEqual(first_event.id, active.id)
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

    def test_event_location_is_optional(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Sem local",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )

        self.assertFalse(EventLocation.objects.filter(event=event).exists())

    def test_event_location_requires_complete_address(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Local incompleto",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        location = EventLocation(
            event=event,
            name="Casa",
            street="",
            number="123",
            neighborhood="Bairro",
            city="Cidade",
            state="SP",
            postal_code="01001000",
            latitude="23.550000",
            longitude="-46.633300",
        )

        with self.assertRaises(ValidationError) as raised:
            location.full_clean()

        self.assertIn("street", raised.exception.message_dict)

    def test_event_location_rejects_coordinates_outside_world_bounds(self) -> None:
        now = timezone.now()
        event = Event.objects.create(
            title="Local inválido",
            start_at=now,
            end_at=now + timedelta(hours=3),
            type=EventType.CABULOUS,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        location = EventLocation(
            event=event,
            name="Casa",
            street="Rua A",
            number="123",
            neighborhood="Bairro",
            city="Cidade",
            state="SP",
            postal_code="01001000",
            latitude="90.000001",
            longitude="-180.000001",
        )

        with self.assertRaises(ValidationError) as raised:
            location.full_clean()

        self.assertIn("latitude", raised.exception.message_dict)
        self.assertIn("longitude", raised.exception.message_dict)

    def test_event_location_rejects_invalid_state(self) -> None:
        for state in ("S", "S1", "SPP"):
            with self.subTest(state=state):
                with self.assertRaises(ValidationError) as raised:
                    self.event_location(state=state).full_clean()

                self.assertIn("state", raised.exception.message_dict)

    def test_event_location_rejects_invalid_postal_code(self) -> None:
        for postal_code in (
            "0100100",
            "010010000",
            "0100A000",
            "abc01001-000xyz",
        ):
            with self.subTest(postal_code=postal_code):
                with self.assertRaises(ValidationError) as raised:
                    self.event_location(postal_code=postal_code).full_clean()

                self.assertIn("postal_code", raised.exception.message_dict)

    def test_event_location_rejects_non_brazilian_country(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            self.event_location(country="US").full_clean()

        self.assertIn("country", raised.exception.message_dict)

    def test_event_location_normalizes_valid_brazilian_address(self) -> None:
        location = self.event_location(
            state="sp",
            postal_code="01001-000",
            country="br",
        )

        location.full_clean()

        self.assertEqual(location.state, "SP")
        self.assertEqual(location.postal_code, "01001000")
        self.assertEqual(location.country, "BR")

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
        EventPhoto.objects.create(
            event=event,
            photo=photo_one,
            linked_by=self.creator,
            is_thumbnail=True,
        )

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
        EventPhoto.objects.create(event=event, photo=photo, linked_by=self.creator)
        HighlightPhoto.objects.create(highlight=highlight, photo=photo)

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
