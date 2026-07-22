from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "healthcheck-tests",
        }
    }
)
class HealthcheckTests(TestCase):
    def test_healthcheck_endpoint_returns_ok(self) -> None:
        response = self.client.get(reverse("healthcheck"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "services": {
                    "database": True,
                    "redis": True,
                },
            },
        )
