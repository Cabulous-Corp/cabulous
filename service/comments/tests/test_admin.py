from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from comments.services import create_comment
from events.enums import EventStatus, EventType
from events.models import Event
from users.models import User


def _create_user(username: str = "admin_user", **overrides) -> User:
    defaults = {
        "email": f"{username}@example.com",
        "password": "secret",
        "onboarding_completed_at": timezone.now(),
    }
    defaults.update(overrides)
    return User.objects.create_user(username=username, **defaults)


def _create_event(creator) -> Event:
    start = timezone.now() + timedelta(days=1)
    return Event.objects.create(
        title="Test Event",
        start_at=start,
        end_at=start + timedelta(hours=2),
        type=EventType.CABULOUS,
        creator=creator,
        status=EventStatus.SCHEDULED,
    )


class CommentsAdminRegistrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = _create_user("superadmin", is_staff=True, is_superuser=True)
        cls.author = _create_user("author")
        cls.event = _create_event(cls.author)
        cls.comment = create_comment(
            author=cls.author,
            target_type="events.event",
            target_id=cls.event.id,
            body="Admin test comment",
            parent=None,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_comment_changelist_loads(self):
        """Admin comment list page returns 200."""
        response = self.client.get("/admin/comments/comment/")
        self.assertEqual(response.status_code, 200)

    def test_comment_changelist_query_count_bounded(self):
        """Admin list page uses bounded queries.
        Captured exact count: session, user load, contenttype list,
        count x2, select_related queryset (with author + contenttype),
        permissions x2, event lookup for admin.
        """
        with self.assertNumQueries(9):
            self.client.get("/admin/comments/comment/")
