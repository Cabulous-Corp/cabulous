from datetime import timedelta

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

    def test_event_location_is_optional(self) -> None:
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Sem local",
            start_at=start,
            end_at=start + timedelta(hours=2),
            type=EventType.CASUAL_HANGOUT,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        self.assertFalse(hasattr(event, "location"))

    def test_event_location_complete_address(self) -> None:
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Com local",
            start_at=start,
            end_at=start + timedelta(hours=2),
            type=EventType.CLUB,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        loc = EventLocation.objects.create(
            event=event,
            name="Bar do Zé",
            address="Rua A, 123",
            latitude=-23.550520,
            longitude=-46.633308,
        )
        self.assertEqual(loc.event, event)
        self.assertEqual(event.location, loc)

    def test_creator_is_independent_from_participant(self) -> None:
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Independence",
            start_at=start,
            end_at=start + timedelta(hours=2),
            type=EventType.BARBECUE,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        participant = User.objects.create_user(
            username="p1", email="p1@example.com", password="secret"
        )
        EventParticipant.objects.create(event=event, user=participant)
        self.assertNotIn(participant, User.objects.filter(created_events=event))

    def test_multiple_audiences(self) -> None:
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Multi audience",
            start_at=start,
            end_at=start + timedelta(hours=2),
            type=EventType.FESTIVAL,
            creator=self.creator,
            status=EventStatus.SCHEDULED,
        )
        EventAudience.objects.create(event=event, audience=Audience.ILUMINADOS)
        EventAudience.objects.create(event=event, audience=Audience.VOYEURS)
        self.assertEqual(event.audiences.count(), 2)

    def test_event_photo_reuse_between_events(self) -> None:
        user = User.objects.create_user(
            username="uploader", email="up@example.com", password="secret"
        )
        photo = Photo.objects.create(
            object_key="k1",
            uploader=user,
            taken_on=timezone.now().date(),
            content_type="image/jpeg",
            size_bytes=1024,
        )
        start = timezone.now() + timedelta(days=1)
        e1 = Event.objects.create(
            title="E1", start_at=start, end_at=start + timedelta(hours=1),
            type=EventType.SHOW, creator=self.creator, status=EventStatus.SCHEDULED,
        )
        e2 = Event.objects.create(
            title="E2", start_at=start, end_at=start + timedelta(hours=1),
            type=EventType.SHOW, creator=self.creator, status=EventStatus.SCHEDULED,
        )
        EventPhoto.objects.create(event=e1, photo=photo, is_thumbnail=True)
        EventPhoto.objects.create(event=e2, photo=photo, is_thumbnail=False)
        self.assertEqual(photo.event_photos.count(), 2)

    def test_one_thumbnail_per_event(self) -> None:
        user = User.objects.create_user(
            username="uploader2", email="up2@example.com", password="secret"
        )
        photo1 = Photo.objects.create(
            object_key="k2", uploader=user, taken_on=timezone.now().date(),
            content_type="image/jpeg", size_bytes=1024,
        )
        photo2 = Photo.objects.create(
            object_key="k3", uploader=user, taken_on=timezone.now().date(),
            content_type="image/png", size_bytes=2048,
        )
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Thumb", start_at=start, end_at=start + timedelta(hours=1),
            type=EventType.CINEMA, creator=self.creator, status=EventStatus.SCHEDULED,
        )
        EventPhoto.objects.create(event=event, photo=photo1, is_thumbnail=True)

        with self.assertRaises(IntegrityError), transaction.atomic():
            EventPhoto.objects.create(event=event, photo=photo2, is_thumbnail=True)

    def test_highlight_and_photo_relations(self) -> None:
        user = User.objects.create_user(
            username="huser", email="h@example.com", password="secret"
        )
        photo = Photo.objects.create(
            object_key="k4", uploader=user, taken_on=timezone.now().date(),
            content_type="image/jpeg", size_bytes=1024,
        )
        start = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Highlight test", start_at=start, end_at=start + timedelta(hours=1),
            type=EventType.CABULOUS, creator=self.creator, status=EventStatus.SCHEDULED,
        )
        h = Highlight.objects.create(event=event, author=self.creator, text="Great moment")
        hp = HighlightPhoto.objects.create(highlight=h, photo=photo)
        self.assertEqual(h.photos.count(), 1)
        self.assertEqual(hp.highlight, h)

    def test_active_and_all_managers(self) -> None:
        start = timezone.now() + timedelta(days=1)
        Event.objects.create(
            title="Active", start_at=start, end_at=start + timedelta(hours=1),
            type=EventType.DINNER, creator=self.creator, status=EventStatus.SCHEDULED,
        )
        e2 = Event.objects.create(
            title="SoftDeleted", start_at=start, end_at=start + timedelta(hours=1),
            type=EventType.DINNER, creator=self.creator, status=EventStatus.SCHEDULED,
        )
        e2.soft_delete()
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Event.all_objects.count(), 2)
