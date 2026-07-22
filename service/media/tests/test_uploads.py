from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from media.models import Photo
from users.models import User


class PhotoUploadUrlsTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader",
            email="uploader@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)
        self.url = "/api/media/photos/upload-urls/"

    @patch("media.services.upload_signing._build_s3_client")
    def test_rejects_more_than_fifty_files(self, client_builder: Mock) -> None:
        payload = [{"filename": f"{i}.jpg", "content_type": "image/jpeg"} for i in range(51)]
        response = self.client.post(self.url, {"files": payload}, format="json")
        self.assertEqual(response.status_code, 400)
        client_builder.assert_not_called()

    @patch("media.services.upload_signing._build_s3_client")
    def test_accepts_fifty_files(self, client_builder: Mock) -> None:
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = "https://minio.example.com/signed"
        client_builder.return_value = mock_client

        payload = [{"filename": f"{i}.jpg", "content_type": "image/jpeg"} for i in range(50)]
        response = self.client.post(self.url, {"files": payload}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["photos"]), 50)

    @patch("media.services.upload_signing._build_s3_client")
    def test_accepts_gif(self, client_builder: Mock) -> None:
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = "https://minio.example.com/signed"
        client_builder.return_value = mock_client

        payload = [{"filename": "anim.gif", "content_type": "image/gif"}]
        response = self.client.post(self.url, {"files": payload}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["photos"][0]["headers"]["Content-Type"], "image/gif")

    def test_rejects_non_image(self) -> None:
        payload = [{"filename": "file.txt", "content_type": "text/plain"}]
        response = self.client.post(self.url, {"files": payload}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_rejects_extension_mismatch(self) -> None:
        payload = [{"filename": "file.txt", "content_type": "image/jpeg"}]
        response = self.client.post(self.url, {"files": payload}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_rejects_empty_files(self) -> None:
        response = self.client.post(self.url, {"files": []}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_requires_authentication(self) -> None:
        self.client.force_authenticate(user=None)
        payload = [{"filename": "photo.jpg", "content_type": "image/jpeg"}]
        response = self.client.post(self.url, {"files": payload}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_pending_onboarding_returns_403(self) -> None:
        pending_user = User.objects.create_user(
            username="pending",
            email="pending@example.com",
            password="secret",
        )
        self.client.force_authenticate(pending_user)
        payload = [{"filename": "photo.jpg", "content_type": "image/jpeg"}]
        response = self.client.post(self.url, {"files": payload}, format="json")
        self.assertEqual(response.status_code, 403)


class PhotoConfirmTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="uploader",
            email="uploader@example.com",
            password="secret",
            onboarding_completed_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)
        self.url = "/api/media/photos/confirm/"
        self.base_key = f"media/photos/{self.user.id}"

    @patch("media.services.upload_signing.default_storage")
    def test_rejects_declared_size_above_limit(self, mock_storage: Mock) -> None:
        payload = {
            "files": [
                {
                    "object_key": f"{self.base_key}/abc123.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 26 * 1024 * 1024,
                }
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_prefix(self) -> None:
        payload = {
            "files": [
                {
                    "object_key": "wrong/prefix/photo.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                }
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("media.services.upload_signing.default_storage")
    def test_rejects_mime_mismatch(self, mock_storage: Mock) -> None:
        mock_storage.head.return_value = {
            "content_type": "image/png",
            "content_length": 1024,
        }
        payload = {
            "files": [
                {
                    "object_key": f"{self.base_key}/abc123.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                }
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("media.services.upload_signing.default_storage")
    def test_rejects_head_size_overflow(self, mock_storage: Mock) -> None:
        mock_storage.head.return_value = {
            "content_type": "image/jpeg",
            "content_length": 26 * 1024 * 1024,
        }
        payload = {
            "files": [
                {
                    "object_key": f"{self.base_key}/abc123.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                }
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("media.services.upload_signing.default_storage")
    def test_invalid_object_prevents_batch(self, mock_storage: Mock) -> None:
        def head_side_effect(key: str) -> dict:
            if "bad" in key:
                return {"content_type": "image/png", "content_length": 1024}
            return {"content_type": "image/jpeg", "content_length": 1024}

        mock_storage.head.side_effect = head_side_effect
        payload = {
            "files": [
                {
                    "object_key": f"{self.base_key}/bad.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                },
                {
                    "object_key": f"{self.base_key}/good.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                },
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Photo.objects.count(), 0)

    @patch("media.services.upload_signing.default_storage")
    def test_confirm_creates_photos(self, mock_storage: Mock) -> None:
        mock_storage.head.return_value = {
            "content_type": "image/jpeg",
            "content_length": 1024,
        }
        payload = {
            "files": [
                {
                    "object_key": f"{self.base_key}/abc123.jpg",
                    "taken_on": "2026-07-20",
                    "caption": "First photo",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                },
                {
                    "object_key": f"{self.base_key}/def456.jpg",
                    "taken_on": "2026-07-21",
                    "caption": "Second photo",
                    "content_type": "image/jpeg",
                    "size_bytes": 2048,
                },
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["caption"], "First photo")
        self.assertEqual(response.data[1]["caption"], "Second photo")
        self.assertEqual(Photo.objects.count(), 2)

    @patch("media.services.upload_signing.default_storage")
    def test_confirm_preserves_request_order(self, mock_storage: Mock) -> None:
        def head_side_effect(key: str) -> dict:
            size_map = {"first": 100, "second": 200, "third": 300}
            for label, size in size_map.items():
                if label in key:
                    return {"content_type": "image/jpeg", "content_length": size}
            return {"content_type": "image/jpeg", "content_length": 100}

        mock_storage.head.side_effect = head_side_effect
        payload = {
            "files": [
                {
                    "object_key": f"{self.base_key}/first.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 100,
                },
                {
                    "object_key": f"{self.base_key}/second.jpg",
                    "taken_on": "2026-07-21",
                    "content_type": "image/jpeg",
                    "size_bytes": 200,
                },
                {
                    "object_key": f"{self.base_key}/third.jpg",
                    "taken_on": "2026-07-22",
                    "content_type": "image/jpeg",
                    "size_bytes": 300,
                },
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        keys = [item["object_key"] for item in response.data]
        self.assertEqual(
            keys,
            [
                f"{self.base_key}/first.jpg",
                f"{self.base_key}/second.jpg",
                f"{self.base_key}/third.jpg",
            ],
        )

    def test_requires_authentication(self) -> None:
        self.client.force_authenticate(user=None)
        payload = {
            "files": [
                {
                    "object_key": f"{self.base_key}/abc.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                }
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 401)

    def test_pending_onboarding_returns_403(self) -> None:
        pending_user = User.objects.create_user(
            username="pending",
            email="pending@example.com",
            password="secret",
        )
        self.client.force_authenticate(pending_user)
        payload = {
            "files": [
                {
                    "object_key": "media/photos/fake/photo.jpg",
                    "taken_on": "2026-07-20",
                    "content_type": "image/jpeg",
                    "size_bytes": 1024,
                }
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 403)
