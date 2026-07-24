from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.enums import Audience, EventStatus, EventType
from events.models import (
    Event,
    EventAudience,
    EventParticipant,
    EventPhoto,
    Highlight,
    HighlightPhoto,
)
from media.models import Photo
from users.models import User


def _create_user(username: str, **overrides: object) -> User:
    defaults = {
        "email": f"{username}@example.com",
        "password": "secret",
        "onboarding_completed_at": timezone.now(),
    }
    defaults.update(overrides)
    return User.objects.create_user(username=username, **defaults)  # type: ignore[arg-type]


def _create_event(creator: User, **overrides: object) -> Event:
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


def _create_photo(uploader: User, **overrides: object) -> Photo:
    defaults = {
        "object_key": f"photos/{uploader.username}/{timezone.now().timestamp()}.jpg",
        "uploader": uploader,
        "taken_on": timezone.now().date(),
        "content_type": "image/jpeg",
        "size_bytes": 1024,
    }
    defaults.update(overrides)
    return Photo.objects.create(**defaults)


def _create_event_photo(event: Event, photo: Photo, **overrides: object) -> EventPhoto:
    defaults = {"event": event, "photo": photo}
    defaults.update(overrides)  # type: ignore[arg-type]
    return EventPhoto.objects.create(**defaults)


def _create_highlight(
    event: Event,
    author: User,
    text: str = "Test highlight",
    photos: list[Photo] | None = None,
) -> Highlight:
    hl = Highlight.objects.create(event=event, author=author, text=text)
    if photos:
        HighlightPhoto.objects.bulk_create([HighlightPhoto(highlight=hl, photo=p) for p in photos])
    return hl


# ---------------------------------------------------------------------------
# Create highlights
# ---------------------------------------------------------------------------


class HighlightCreateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.staff = _create_user("staff", is_staff=True)
        self.event = _create_event(self.creator)
        self.photo = _create_photo(self.creator)
        self.url = f"/api/events/{self.event.id}/highlights/"

    def test_creator_can_create_highlight(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.post(self.url, {"text": "Great party!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Highlight.objects.count(), 1)
        hl = Highlight.objects.first()
        self.assertEqual(hl.text, "Great party!")  # type: ignore[union-attr]
        self.assertEqual(hl.author, self.creator)  # type: ignore[union-attr]

    def test_participant_can_create_highlight(self) -> None:
        EventParticipant.objects.create(event=self.event, user=self.other)
        self.client.force_authenticate(self.other)  # type: ignore[attr-defined]
        response = self.client.post(self.url, {"text": "Awesome!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_staff_can_create_highlight(self) -> None:
        self.client.force_authenticate(self.staff)  # type: ignore[attr-defined]
        response = self.client.post(self.url, {"text": "Staff says hi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_cannot_create_highlight(self) -> None:
        stranger = _create_user("stranger")
        self.client.force_authenticate(stranger)  # type: ignore[attr-defined]
        response = self.client.post(self.url, {"text": "Hacked!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_text_500_accepted(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.post(self.url, {"text": "x" * 500}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_text_501_rejected(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.post(self.url, {"text": "x" * 501}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_linked_photos(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        photo2 = _create_photo(self.creator, object_key="photos/creator/p2.jpg")
        _create_event_photo(self.event, self.photo)
        _create_event_photo(self.event, photo2)
        response = self.client.post(
            self.url,
            {
                "text": "With photos!",
                "photo_ids": [str(self.photo.id), str(photo2.id)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        hl = Highlight.objects.first()
        self.assertEqual(hl.photos.count(), 2)  # type: ignore[union-attr]

    def test_create_with_unlinked_photo_rejected(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.post(
            self.url,
            {"text": "Has fake photo!", "photo_ids": [fake_id]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Highlight.objects.count(), 0)

    def test_create_with_mixed_photos_partial_failure(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.post(
            self.url,
            {
                "text": "Mixed photos",
                "photo_ids": [str(self.photo.id), fake_id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Highlight should NOT be created on partial failure
        self.assertEqual(Highlight.objects.count(), 0)

    def test_highlight_from_another_event_404(self) -> None:
        """A highlight UUID scoped to another event returns 404."""
        other_event = _create_event(self.other, title="Other Event")
        hl = _create_highlight(other_event, self.other)
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.get(f"{self.url}{hl.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_401(self) -> None:
        response = self.client.post(self.url, {"text": "Anon"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# List highlights
# ---------------------------------------------------------------------------


class HighlightListTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.event = _create_event(self.creator)
        self.url = f"/api/events/{self.event.id}/highlights/"
        self.client.force_authenticate(self.creator)

        self.hl1 = _create_highlight(self.event, self.creator, text="First")
        self.hl2 = _create_highlight(self.event, self.creator, text="Second")

    def test_list_returns_highlights(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # type: ignore[attr-defined]

    def test_list_includes_photos(self) -> None:
        photo = _create_photo(self.creator)
        HighlightPhoto.objects.create(highlight=self.hl1, photo=photo)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["results"][0]["photos"]), 1)  # type: ignore[attr-defined]

    def test_list_photos_include_photo_details(self) -> None:
        photo = _create_photo(self.creator, caption="Sunset")
        HighlightPhoto.objects.create(highlight=self.hl1, photo=photo)
        response = self.client.get(self.url)
        pdata = response.data["results"][0]["photos"][0]  # type: ignore[attr-defined]
        self.assertEqual(pdata["id"], str(photo.id))
        self.assertEqual(pdata["object_key"], photo.object_key)
        self.assertEqual(pdata["content_type"], photo.content_type)

    def test_list_photos_stable_order(self) -> None:
        p1 = _create_photo(self.creator, object_key="p1.jpg")
        p2 = _create_photo(self.creator, object_key="p2.jpg")
        HighlightPhoto.objects.create(highlight=self.hl1, photo=p1)
        HighlightPhoto.objects.create(highlight=self.hl1, photo=p2)
        response = self.client.get(self.url)
        ids = [p["id"] for p in response.data["results"][0]["photos"]]  # type: ignore[attr-defined]
        # p1 was created before p2, so it should be first
        self.assertEqual(ids, [str(p1.id), str(p2.id)])


# ---------------------------------------------------------------------------
# Update highlights
# ---------------------------------------------------------------------------


class HighlightUpdateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.staff = _create_user("staff", is_staff=True)
        self.event = _create_event(self.creator)
        self.photo = _create_photo(self.creator)
        EventParticipant.objects.create(event=self.event, user=self.other)
        self.hl = _create_highlight(self.event, self.creator, text="Original")
        self.other_hl = _create_highlight(self.event, self.other, text="Other's highlight")
        self.url = f"/api/events/{self.event.id}/highlights/{self.hl.id}/"

    def test_author_can_patch_text(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.patch(self.url, {"text": "Updated text"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.hl.refresh_from_db()
        self.assertEqual(self.hl.text, "Updated text")

    def test_creator_can_patch_others_highlight(self) -> None:
        url = f"/api/events/{self.event.id}/highlights/{self.other_hl.id}/"
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.patch(url, {"text": "Edited by creator"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_can_patch_any_highlight(self) -> None:
        self.client.force_authenticate(self.staff)  # type: ignore[attr-defined]
        response = self.client.patch(self.url, {"text": "Staff edit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_author_participant_cannot_patch_others(self) -> None:
        # other is not the author of self.hl (creator is)
        self.client.force_authenticate(self.other)  # type: ignore[attr-defined]
        response = self.client.patch(self.url, {"text": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_replace_photos(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        photo2 = _create_photo(self.creator, object_key="photos/creator/p2.jpg")
        _create_event_photo(self.event, self.photo)
        _create_event_photo(self.event, photo2)
        # First create with one photo
        photo_hl = _create_highlight(self.event, self.creator, photos=[self.photo])
        url = f"/api/events/{self.event.id}/highlights/{photo_hl.id}/"
        # Replace with a different photo
        response = self.client.patch(url, {"photo_ids": [str(photo2.id)]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        photo_hl.refresh_from_db()
        self.assertEqual(photo_hl.photos.count(), 1)
        self.assertEqual(photo_hl.photos.first().photo_id, photo2.id)  # type: ignore[union-attr]

    def test_update_remove_all_photos(self) -> None:
        photo_hl = _create_highlight(self.event, self.creator, photos=[self.photo])
        url = f"/api/events/{self.event.id}/highlights/{photo_hl.id}/"
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.patch(url, {"photo_ids": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        photo_hl.refresh_from_db()
        self.assertEqual(photo_hl.photos.count(), 0)

    def test_update_with_invalid_photo_rejected(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.patch(self.url, {"photo_ids": [fake_id]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Delete highlights
# ---------------------------------------------------------------------------


class HighlightDeleteTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.other = _create_user("other")
        self.staff = _create_user("staff", is_staff=True)
        self.event = _create_event(self.creator)
        self.photo = _create_photo(self.creator)
        EventParticipant.objects.create(event=self.event, user=self.other)
        self.hl = _create_highlight(self.event, self.creator, text="To delete")
        self.other_hl = _create_highlight(self.event, self.other, text="Other's")
        self.url = f"/api/events/{self.event.id}/highlights/{self.hl.id}/"

    def test_author_can_delete(self) -> None:
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Highlight.objects.filter(id=self.hl.id).exists())

    def test_creator_can_delete_others_highlight(self) -> None:
        url = f"/api/events/{self.event.id}/highlights/{self.other_hl.id}/"
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_staff_can_delete_any(self) -> None:
        self.client.force_authenticate(self.staff)  # type: ignore[attr-defined]
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_author_participant_cannot_delete_others(self) -> None:
        self.client.force_authenticate(self.other)  # type: ignore[attr-defined]
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_does_not_delete_photo(self) -> None:
        """Physical delete of Highlight must NOT delete Photo objects."""
        hl = _create_highlight(self.event, self.creator, photos=[self.photo])
        self.assertEqual(HighlightPhoto.objects.count(), 1)
        self.assertEqual(Photo.objects.count(), 1)

        url = f"/api/events/{self.event.id}/highlights/{hl.id}/"
        self.client.force_authenticate(self.creator)  # type: ignore[attr-defined]
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # HighlightPhoto records are gone (cascade from highlight)
        self.assertEqual(HighlightPhoto.objects.count(), 0)
        # Photo still exists
        self.assertEqual(Photo.objects.count(), 1)
        self.assertTrue(Photo.objects.filter(id=self.photo.id).exists())


# ---------------------------------------------------------------------------
# Retrieve single highlight
# ---------------------------------------------------------------------------


class HighlightRetrieveTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.creator = _create_user("creator")
        self.event = _create_event(self.creator)
        self.photo = _create_photo(self.creator)
        self.hl = _create_highlight(self.event, self.creator, text="Single", photos=[self.photo])
        self.url = f"/api/events/{self.event.id}/highlights/{self.hl.id}/"
        self.client.force_authenticate(self.creator)

    def test_retrieve_returns_highlight(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Single")  # type: ignore[attr-defined]
        self.assertEqual(response.data["id"], str(self.hl.id))  # type: ignore[attr-defined]

    def test_retrieve_includes_photos(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["photos"]), 1)  # type: ignore[attr-defined]
        self.assertEqual(response.data["photos"][0]["id"], str(self.photo.id))  # type: ignore[attr-defined]

    def test_retrieve_404_from_other_event(self) -> None:
        other_event = _create_event(self.creator, title="Other")
        response = self.client.get(f"/api/events/{other_event.id}/highlights/{self.hl.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
