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
