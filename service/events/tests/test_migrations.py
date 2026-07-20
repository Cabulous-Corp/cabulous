from datetime import timedelta
from typing import Any

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class EventMigrationTests(TransactionTestCase):
    migrate_from = "0001_initial"
    migrate_to = "0002_event_domain"

    def _targets(self, event_target: str) -> list[tuple[str, str]]:
        executor = MigrationExecutor(connection)
        targets = [
            node
            for node in executor.loader.graph.leaf_nodes()
            if node[0] not in {"events", "media", "users"}
        ]
        return [
            *targets,
            ("users", "0001_initial"),
            ("media", "0001_initial"),
            ("events", event_target),
        ]

    def _migrate(self, event_target: str) -> Any:
        executor = MigrationExecutor(connection)
        targets = self._targets(event_target)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def setUp(self) -> None:
        super().setUp()
        self.old_apps = self._migrate(self.migrate_from)
        self.old_apps.get_model("events", "Event").objects.all().delete()
        self.old_apps.get_model("users", "User").objects.all().delete()

    def tearDown(self) -> None:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _create_legacy_event(self, **overrides: Any) -> Any:
        now = timezone.now()
        values = {
            "title": "Legacy event",
            "description": "",
            "start_at": now + timedelta(days=1),
            "end_at": now + timedelta(days=2),
            "type": "CABULOUS",
            "public": "VOYEURS",
        }
        values.update(overrides)
        return self.old_apps.get_model("events", "Event").objects.create(**values)

    def test_empty_database_migrates_forward_and_back(self) -> None:
        new_apps = self._migrate(self.migrate_to)
        self.assertEqual(new_apps.get_model("events", "EventAudience").objects.count(), 0)

        reversed_apps = self._migrate(self.migrate_from)
        self.assertIsNotNone(reversed_apps.get_model("events", "Event")._meta.get_field("public"))

    def test_forward_uses_historical_user_and_preserves_legacy_data(self) -> None:
        HistoricalUser = self.old_apps.get_model("users", "User")
        creator = HistoricalUser.objects.create(
            username="legacy-creator",
            email="legacy@example.com",
            is_superuser=True,
        )
        legacy_event = self._create_legacy_event()

        new_apps = self._migrate(self.migrate_to)
        Event = new_apps.get_model("events", "Event")
        EventAudience = new_apps.get_model("events", "EventAudience")
        migrated_event = Event.objects.get(pk=legacy_event.pk)

        self.assertEqual(migrated_event.creator_id, creator.pk)
        self.assertEqual(migrated_event.status, "SCHEDULED")
        self.assertTrue(
            EventAudience.objects.filter(event_id=legacy_event.pk, audience="VOYEURS").exists()
        )

    def test_reverse_restores_first_audience_by_created_at_and_id(self) -> None:
        HistoricalUser = self.old_apps.get_model("users", "User")
        HistoricalUser.objects.create(
            username="legacy-creator",
            email="legacy@example.com",
            is_superuser=True,
        )
        legacy_event = self._create_legacy_event(public="ILUMINADOS")
        new_apps = self._migrate(self.migrate_to)
        EventAudience = new_apps.get_model("events", "EventAudience")
        EventAudience.objects.create(event_id=legacy_event.pk, audience="OTHERS")

        reversed_apps = self._migrate(self.migrate_from)
        reversed_event = reversed_apps.get_model("events", "Event").objects.get(pk=legacy_event.pk)

        self.assertEqual(reversed_event.public, "ILUMINADOS")

    def test_reverse_restores_audience_for_soft_deleted_event(self) -> None:
        HistoricalUser = self.old_apps.get_model("users", "User")
        HistoricalUser.objects.create(
            username="legacy-creator",
            email="legacy@example.com",
            is_superuser=True,
        )
        legacy_event = self._create_legacy_event(public="VOYEURS")
        new_apps = self._migrate(self.migrate_to)
        Event = new_apps.get_model("events", "Event")
        Event.all_objects.filter(pk=legacy_event.pk).update(deleted_at=timezone.now())

        reversed_apps = self._migrate(self.migrate_from)
        reversed_event = reversed_apps.get_model("events", "Event").objects.get(pk=legacy_event.pk)

        self.assertEqual(reversed_event.public, "VOYEURS")
