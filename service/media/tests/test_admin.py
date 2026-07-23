from datetime import date

from django.test import TestCase
from django.utils import timezone

from media.models import Photo
from users.models import User


def _create_user(username: str = "admin_user", **overrides: object) -> User:
    defaults = {
        "email": f"{username}@example.com",
        "password": "secret",
        "onboarding_completed_at": timezone.now(),
    }
    defaults.update(overrides)
    return User.objects.create_user(username=username, **defaults)


class MediaAdminRegistrationTests(TestCase):
    admin_user: User
    uploader: User
    photo: Photo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = _create_user("superadmin", is_staff=True, is_superuser=True)
        cls.uploader = _create_user("uploader")
        cls.photo = Photo.objects.create(
            object_key="media/photos/test/img.jpg",
            uploader=cls.uploader,
            taken_on=date(2026, 7, 20),
            content_type="image/jpeg",
            size_bytes=2048,
        )

    def setUp(self) -> None:
        self.client.force_login(self.admin_user)

    def test_photo_changelist_loads(self) -> None:
        """Admin photo list page returns 200."""
        response = self.client.get("/admin/media/photo/")
        self.assertEqual(response.status_code, 200)

    def test_photo_changelist_query_count_bounded(self) -> None:
        """Admin list page uses bounded queries.
        Captured exact count: session, user load, contenttype list,
        count x2, select_related queryset (with uploader),
        permissions x3, contenttype for admin.
        """
        with self.assertNumQueries(8):
            self.client.get("/admin/media/photo/")
