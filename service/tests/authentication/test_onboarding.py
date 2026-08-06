from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from authentication.serializers import OnboardingFirstAccessSerializer
from users.models import User


def onboarding_data(**overrides: str) -> dict[str, str]:
    data = {
        "new_password": "Cabulous!2026",
        "email": "pending@example.com",
        "username": "pending",
        "first_name": "Pending",
        "last_name": "User",
    }
    data.update(overrides)
    return data


class OnboardingFirstAccessSerializerTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="pending",
            email="pending@example.com",
            password="Bootstrap!2026",
            onboarding_completed_at=None,
        )

    def test_accepts_strong_password_and_existing_username(self) -> None:
        serializer = OnboardingFirstAccessSerializer(
            instance=self.user,
            data=onboarding_data(),
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_password_variants(self) -> None:
        invalid_passwords = {
            "short": "short",
            "common": "admin1234",
            "similar": "Pending123!",
            "numeric": "12345678",
        }

        for label, password in invalid_passwords.items():
            with self.subTest(label=label):
                serializer = OnboardingFirstAccessSerializer(
                    instance=self.user,
                    data=onboarding_data(new_password=password),
                    partial=True,
                )

                self.assertFalse(serializer.is_valid())
                self.assertIn("new_password", serializer.errors)

    def test_rejects_invalid_profile_fields(self) -> None:
        serializer = OnboardingFirstAccessSerializer(
            instance=self.user,
            data=onboarding_data(username="@pending", phone_number="000"),
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertIn("phone_number", serializer.errors)

    def test_requires_new_password(self) -> None:
        data = onboarding_data()
        del data["new_password"]
        serializer = OnboardingFirstAccessSerializer(
            instance=self.user,
            data=data,
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)

    def test_update_completes_onboarding(self) -> None:
        serializer = OnboardingFirstAccessSerializer(
            instance=self.user,
            data=onboarding_data(),
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.onboarding_completed_at)
        self.assertIsNotNone(self.user.password_defined_at)
        self.assertTrue(self.user.check_password("Cabulous!2026"))


class OnboardingFirstAccessApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="Bootstrap!2026",
            onboarding_completed_at=None,
        )
        self.url = "/api/auth/onboarding/complete/"
        self.client.force_authenticate(self.user)

    def test_returns_structured_password_validation_error(self) -> None:
        response = self.client.post(
            self.url,
            onboarding_data(
                new_password="Admin123!",
                email=self.user.email,
                username=self.user.username,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn("new_password", response_data)
        self.assertIn("Nome de usuário", str(response_data["new_password"]))

    def test_completes_onboarding_end_to_end(self) -> None:
        response = self.client.post(
            self.url,
            onboarding_data(
                email=self.user.email,
                username=self.user.username,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        completed_at = self.user.onboarding_completed_at
        self.assertIsNotNone(completed_at)
        assert completed_at is not None
        self.assertGreaterEqual(
            completed_at,
            timezone.now() - timedelta(seconds=5),
        )
