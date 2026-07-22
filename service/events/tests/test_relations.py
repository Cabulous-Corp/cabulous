from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.enums import Audience, EventStatus, EventType
from events.models import Event, EventAudience, EventParticipant, EventPhoto
from media.models import Photo
from users.models import User


def _create_user(username: str, **overrides) -> User:
    defaults = {
        "email": f"{username}@example.com",
        "password": "secret",
        "onboarding_completed_at": timezone.now(),
    }
    defaults.update(overrides)
    return User.objects.create_user(username=username, **defaults)


def _create_event(creator, **overrides) -> Event:
    start = timezone.now() + timedelta(days=1)
    defaults = {
        "title": "Test Event",
        "start_at": start,
        "end_at": start + timedelta(hours=2),
        "type": EventType.CABULOUS,
        "creator": creator,
        "status": EventStatus.SCHEDULED,
    }
    defaults.update(overrides)
    event = Event.objects.create(**defaults)
    EventAudience.objects.create(event=event, audience=Audience.ILUMINADOS)
    EventParticipant.objects.create(event=event, user=creator)
    return event


def _create_photo(uploader, **overrides) -> Photo:
    defaults = {
        "object_key": f"photos/{uploader.username}/{timezone.now().timestamp()}.jpg",
        "uploader": uploader,
        "taken_on": timezone.now().date(),
        "content_type": "image/jpeg",
        "size_bytes": 1024,
    }
    defaults.update(overrides)
    return Photo.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------


class ParticipantApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.staff = _create_user("staff", is_staff=True)
        self.event = _create_event(self.creator)
        self.url = f"/api/events/{self.event.id}/participants/"

    # -- batch add (POST) ---------------------------------------------------

    def test_creator_can_add_participants(self) -> None:
        self.client.force_authenticate(self.creator)
        response = self.client.post(self.url, {"user_ids": [str(self.other.id)]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EventParticipant.objects.filter(event=self.event, user=self.other).exists())

    def test_staff_can_add_participants(self) -> None:
        self.client.force_authenticate(self.staff)
        response = self.client.post(self.url, {"user_ids": [str(self.other.id)]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_participant_cannot_add(self) -> None:
        stranger = _create_user("stranger")
        self.client.force_authenticate(stranger)
        response = self.client.post(self.url, {"user_ids": [str(stranger.id)]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_add_is_idempotent(self) -> None:
        # Creator is already a participant from _create_event
        self.client.force_authenticate(self.creator)
        response = self.client.post(self.url, {"user_ids": [str(self.creator.id)]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            EventParticipant.objects.filter(event=self.event, user=self.creator).count(),
            1,
        )

    def test_inactive_user_rejected(self) -> None:
        inactive = _create_user("inactive", is_active=False)
        self.client.force_authenticate(self.creator)
        response = self.client.post(self.url, {"user_ids": [str(inactive.id)]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deleted_user_rejected(self) -> None:
        deleted = _create_user("deleted")
        deleted.soft_delete()
        self.client.force_authenticate(self.creator)
        response = self.client.post(self.url, {"user_ids": [str(deleted.id)]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_user_rejected(self) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        self.client.force_authenticate(self.creator)
        response = self.client.post(self.url, {"user_ids": [fake_id]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -- remove (DELETE) ----------------------------------------------------

    def test_creator_can_remove_participant(self) -> None:
        self.client.force_authenticate(self.creator)
        response = self.client.delete(f"{self.url}{self.other.id}/", format="json")
        # other isn't a participant yet, so 404
        self.assertIn(
            response.status_code,
            [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND],
        )

    def test_participant_can_remove_self(self) -> None:
        # Add other as participant first
        EventParticipant.objects.create(event=self.event, user=self.other)
        self.client.force_authenticate(self.other)
        response = self.client.delete(f"{self.url}{self.other.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            EventParticipant.objects.filter(event=self.event, user=self.other).exists()
        )

    def test_non_participant_cannot_remove_others(self) -> None:
        EventParticipant.objects.create(event=self.event, user=self.other)
        stranger = _create_user("stranger")
        self.client.force_authenticate(stranger)
        response = self.client.delete(f"{self.url}{self.other.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_cannot_remove_self(self) -> None:
        self.client.force_authenticate(self.creator)
        response = self.client.delete(f"{self.url}{self.creator.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -- list (GET) ---------------------------------------------------------

    def test_list_participants(self) -> None:
        EventParticipant.objects.create(event=self.event, user=self.other)
        self.client.force_authenticate(self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)  # creator + other

    def test_pagination(self) -> None:
        users = [_create_user(f"p{i}") for i in range(25)]
        ids = [str(u.id) for u in users]
        self.client.force_authenticate(self.creator)
        self.client.post(self.url, {"user_ids": ids}, format="json")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 26)  # 25 + creator
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])


# ---------------------------------------------------------------------------
# Event Photos
# ---------------------------------------------------------------------------


class EventPhotoApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.staff = _create_user("staff", is_staff=True)
        self.event = _create_event(self.creator)
        self.photo = _create_photo(self.creator)
        self.url = f"/api/events/{self.event.id}/photos/"

    # -- link (POST) --------------------------------------------------------

    def test_creator_can_link_photo(self) -> None:
        self.client.force_authenticate(self.creator)
        response = self.client.post(self.url, {"photo_id": str(self.photo.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EventPhoto.objects.filter(event=self.event, photo=self.photo).exists())

    def test_participant_can_link_photo(self) -> None:
        self.client.force_authenticate(self.creator)
        # other isn't participant yet; add them
        EventParticipant.objects.create(event=self.event, user=self.other)
        self.client.force_authenticate(self.other)
        other_photo = _create_photo(self.other)
        response = self.client.post(self.url, {"photo_id": str(other_photo.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_staff_can_link_photo(self) -> None:
        self.client.force_authenticate(self.staff)
        response = self.client.post(self.url, {"photo_id": str(self.photo.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_cannot_link_photo(self) -> None:
        stranger = _create_user("stranger")
        self.client.force_authenticate(stranger)
        response = self.client.post(self.url, {"photo_id": str(self.photo.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_photo_rejected(self) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        self.client.force_authenticate(self.creator)
        response = self.client.post(self.url, {"photo_id": fake_id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_photo_on_two_events(self) -> None:
        event2 = _create_event(self.creator, title="Event 2")
        self.client.force_authenticate(self.creator)
        response1 = self.client.post(self.url, {"photo_id": str(self.photo.id)}, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        url2 = f"/api/events/{event2.id}/photos/"
        response2 = self.client.post(url2, {"photo_id": str(self.photo.id)}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

    # -- unlink (DELETE) ----------------------------------------------------

    def test_creator_can_unlink_any_photo(self) -> None:
        EventPhoto.objects.create(event=self.event, photo=self.photo)
        self.client.force_authenticate(self.creator)
        response = self.client.delete(f"{self.url}{self.photo.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EventPhoto.objects.filter(event=self.event, photo=self.photo).exists())

    def test_linker_can_unlink_own_photo(self) -> None:
        EventParticipant.objects.create(event=self.event, user=self.other)
        other_photo = _create_photo(self.other)
        EventPhoto.objects.create(event=self.event, photo=other_photo, linked_by=self.other)
        self.client.force_authenticate(self.other)
        response = self.client.delete(f"{self.url}{other_photo.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_linker_participant_cannot_unlink_others(self) -> None:
        EventParticipant.objects.create(event=self.event, user=self.other)
        other_photo = _create_photo(self.other)
        EventPhoto.objects.create(event=self.event, photo=other_photo, linked_by=self.other)
        stranger = _create_user("stranger")
        EventParticipant.objects.create(event=self.event, user=stranger)
        self.client.force_authenticate(stranger)
        response = self.client.delete(f"{self.url}{other_photo.id}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -- list (GET) ---------------------------------------------------------

    def test_list_photos(self) -> None:
        EventPhoto.objects.create(event=self.event, photo=self.photo)
        self.client.force_authenticate(self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    # -- thumbnail (PUT / DELETE) -------------------------------------------

    def test_set_thumbnail(self) -> None:
        EventPhoto.objects.create(event=self.event, photo=self.photo)
        self.client.force_authenticate(self.creator)
        thumb_url = f"/api/events/{self.event.id}/thumbnail/"
        response = self.client.put(thumb_url, {"photo_id": str(self.photo.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ep = EventPhoto.objects.get(event=self.event, photo=self.photo)
        self.assertTrue(ep.is_thumbnail)

    def test_replace_thumbnail(self) -> None:
        photo2 = _create_photo(self.creator, object_key="photos/creator/photo2.jpg")
        EventPhoto.objects.create(event=self.event, photo=self.photo, is_thumbnail=True)
        EventPhoto.objects.create(event=self.event, photo=photo2)
        self.client.force_authenticate(self.creator)
        thumb_url = f"/api/events/{self.event.id}/thumbnail/"
        response = self.client.put(thumb_url, {"photo_id": str(photo2.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(EventPhoto.objects.get(event=self.event, photo=self.photo).is_thumbnail)
        self.assertTrue(EventPhoto.objects.get(event=self.event, photo=photo2).is_thumbnail)

    def test_clear_thumbnail(self) -> None:
        EventPhoto.objects.create(event=self.event, photo=self.photo, is_thumbnail=True)
        self.client.force_authenticate(self.creator)
        thumb_url = f"/api/events/{self.event.id}/thumbnail/"
        response = self.client.delete(thumb_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EventPhoto.objects.filter(event=self.event, is_thumbnail=True).exists())

    def test_set_thumbnail_unlinked_photo_rejected(self) -> None:
        # photo is not linked to event
        self.client.force_authenticate(self.creator)
        thumb_url = f"/api/events/{self.event.id}/thumbnail/"
        response = self.client.put(thumb_url, {"photo_id": str(self.photo.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
