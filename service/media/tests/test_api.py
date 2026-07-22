from datetime import date
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from events.enums import EventStatus, EventType
from events.models import Event, EventPhoto
from media.models import Photo
from users.models import User


def _create_photo(user: User, **overrides) -> Photo:
    defaults = {
        "object_key": f"media/photos/{user.id}/{timezone.now().timestamp()}.jpg",
        "uploader": user,
        "taken_on": date(2026, 7, 20),
        "content_type": "image/jpeg",
        "size_bytes": 1024,
    }
    defaults.update(overrides)
    return Photo.objects.create(**defaults)


class PhotoListPermissionTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/media/photos/"

    def test_anonymous_list_returns_401(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_pending_onboarding_returns_403(self) -> None:
        pending_user = User.objects.create_user(
            username="pending", email="p@example.com", password="secret"
        )
        self.client.force_authenticate(pending_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list_returns_own_photos_only(self) -> None:
        user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        other = User.objects.create_user(
            username="other", email="o@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        _create_photo(user, object_key="media/photos/user1/a.jpg")
        _create_photo(other, object_key="media/photos/user2/b.jpg")

        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["object_key"], "media/photos/user1/a.jpg")


class PhotoRetrievePermissionTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            username="other", email="o@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_retrieve_own_photo_succeeds(self) -> None:
        photo = _create_photo(self.user, object_key="media/photos/user1/own.jpg")
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 200)

    def test_retrieve_other_photo_returns_403(self) -> None:
        photo = _create_photo(self.other, object_key="media/photos/user2/other.jpg")
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 403)


class PhotoUpdatePermissionTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            username="other", email="o@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )

    def test_partial_update_own_photo_succeeds(self) -> None:
        photo = _create_photo(self.user, object_key="media/photos/user1/own.jpg")
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/media/photos/{photo.id}/", {"caption": "Updated"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        photo.refresh_from_db()
        self.assertEqual(photo.caption, "Updated")

    def test_partial_update_other_photo_returns_403(self) -> None:
        photo = _create_photo(self.other, object_key="media/photos/user2/other.jpg")
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/media/photos/{photo.id}/", {"caption": "Hacked"}, format="json"
        )
        self.assertEqual(response.status_code, 403)


class PhotoDestroyPermissionTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            username="other", email="o@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )

    @patch("media.services.deletion.default_storage")
    def test_destroy_own_photo_succeeds(self, mock_storage: Mock) -> None:
        mock_storage.delete.return_value = True
        photo = _create_photo(self.user, object_key="media/photos/user1/own.jpg")
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Photo.objects.filter(id=photo.id).exists())

    def test_destroy_other_photo_returns_403(self) -> None:
        photo = _create_photo(self.other, object_key="media/photos/user2/other.jpg")
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Photo.objects.filter(id=photo.id).exists())


class PhotoStaffOverrideTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="secret",
            is_staff=True, onboarding_completed_at=timezone.now(),
        )

    def test_staff_can_retrieve_any_photo(self) -> None:
        photo = _create_photo(self.owner, object_key="media/photos/owner/a.jpg")
        self.client.force_authenticate(self.staff)
        response = self.client.get(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 200)

    def test_staff_can_update_any_photo(self) -> None:
        photo = _create_photo(self.owner, object_key="media/photos/owner/b.jpg")
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            f"/api/media/photos/{photo.id}/", {"caption": "Staff edit"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        photo.refresh_from_db()
        self.assertEqual(photo.caption, "Staff edit")

    @patch("media.services.deletion.default_storage")
    def test_staff_can_delete_any_photo(self, mock_storage: Mock) -> None:
        mock_storage.delete.return_value = True
        photo = _create_photo(self.owner, object_key="media/photos/owner/c.jpg")
        self.client.force_authenticate(self.staff)
        response = self.client.delete(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Photo.objects.filter(id=photo.id).exists())


class PhotoPaginationTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)

    def test_pagination_page_size_20(self) -> None:
        for i in range(25):
            _create_photo(
                self.user,
                object_key=f"media/photos/{self.user.id}/page{i}.jpg",
                taken_on=date(2026, 1, 1),
            )
        response = self.client.get("/api/media/photos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])

        response2 = self.client.get(response.data["next"])
        self.assertEqual(len(response2.data["results"]), 5)
        self.assertIsNone(response2.data["next"])


class PhotoOrderingTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)

    def test_ordering_by_date_desc(self) -> None:
        _create_photo(self.user, object_key="m/p/1.jpg", taken_on=date(2026, 7, 1))
        _create_photo(self.user, object_key="m/p/2.jpg", taken_on=date(2026, 7, 10))
        _create_photo(self.user, object_key="m/p/3.jpg", taken_on=date(2026, 7, 5))

        response = self.client.get("/api/media/photos/")
        dates = [item["taken_on"] for item in response.data["results"]]
        self.assertEqual(dates, ["2026-07-10", "2026-07-05", "2026-07-01"])


class PhotoFilterTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            username="other", email="o@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)

        self.p1 = _create_photo(
            self.user, object_key="m/p/a.jpg",
            taken_on=date(2026, 7, 1), caption="Beach party",
        )
        self.p2 = _create_photo(
            self.user, object_key="m/p/b.jpg",
            taken_on=date(2026, 7, 15), caption="Mountain hike",
        )
        self.p3 = _create_photo(
            self.other, object_key="m/p/c.jpg",
            taken_on=date(2026, 7, 10), caption="Beach sunset",
        )

    def test_filter_taken_from(self) -> None:
        response = self.client.get("/api/media/photos/", {"taken_from": "2026-07-10"})
        ids = {item["id"] for item in response.data["results"]}
        self.assertIn(str(self.p2.id), ids)
        self.assertNotIn(str(self.p1.id), ids)

    def test_filter_taken_until(self) -> None:
        response = self.client.get("/api/media/photos/", {"taken_until": "2026-07-05"})
        ids = {item["id"] for item in response.data["results"]}
        self.assertIn(str(self.p1.id), ids)
        self.assertNotIn(str(self.p2.id), ids)

    def test_filter_uploader(self) -> None:
        response = self.client.get("/api/media/photos/", {"uploader": str(self.other.id)})
        ids = {item["id"] for item in response.data["results"]}
        # other's photos are not in the user's list queryset
        self.assertNotIn(str(self.p3.id), ids)

    def test_filter_event(self) -> None:
        event = Event.objects.create(
            title="Party", start_at=timezone.now(), end_at=timezone.now(),
            type=EventType.CASUAL_HANGOUT, creator=self.user, status=EventStatus.SCHEDULED,
        )
        EventPhoto.objects.create(event=event, photo=self.p1)
        response = self.client.get("/api/media/photos/", {"event": str(event.id)})
        ids = {item["id"] for item in response.data["results"]}
        self.assertIn(str(self.p1.id), ids)
        self.assertNotIn(str(self.p2.id), ids)

    def test_filter_search_caption(self) -> None:
        response = self.client.get("/api/media/photos/", {"search": "Beach"})
        ids = {item["id"] for item in response.data["results"]}
        self.assertIn(str(self.p1.id), ids)
        self.assertNotIn(str(self.p2.id), ids)


class PhotoHardDeleteTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader", email="u@example.com", password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)

    @patch("media.services.deletion.default_storage")
    def test_hard_delete_removes_from_storage_and_db(self, mock_storage: Mock) -> None:
        mock_storage.delete.return_value = True
        photo = _create_photo(self.user, object_key="media/photos/user1/delete_me.jpg")
        response = self.client.delete(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 204)
        mock_storage.delete.assert_called_once_with("media/photos/user1/delete_me.jpg")
        self.assertFalse(Photo.objects.filter(id=photo.id).exists())

    @patch("media.services.deletion.default_storage")
    def test_hard_delete_storage_error_returns_503(self, mock_storage: Mock) -> None:
        mock_storage.delete.side_effect = Exception("Storage unavailable")
        photo = _create_photo(self.user, object_key="media/photos/user1/fail.jpg")
        response = self.client.delete(f"/api/media/photos/{photo.id}/")
        self.assertEqual(response.status_code, 503)
        self.assertTrue(Photo.objects.filter(id=photo.id).exists())
