from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from comments.services import create_comment, soft_delete_comment
from events.enums import EventStatus, EventType
from events.models import Event


def _make_event(creator, **overrides) -> Event:
    defaults = {
        "title": "Test Event",
        "description": "",
        "start_at": timezone.now() + timedelta(days=1),
        "end_at": timezone.now() + timedelta(days=2),
        "type": EventType.CLUB,
        "status": EventStatus.SCHEDULED,
    }
    defaults.update(overrides)
    return Event.objects.create(creator=creator, **defaults)


class CommentDomainTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        from users.models import User

        cls.user = User.objects.create_user(
            username="commenter",
            email="commenter@example.com",
            password="pass",
        )

    def setUp(self) -> None:
        self.event_a = _make_event(self.user)
        self.event_b = _make_event(self.user)

    def test_child_must_share_parent_target(self) -> None:
        parent = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event_a.id,
            body="Parent comment",
            parent=None,
        )
        with self.assertRaises(ValidationError):
            create_comment(
                author=self.user,
                target_type="events.event",
                target_id=self.event_b.id,
                body="Child comment",
                parent=parent,
            )

    def test_unknown_target_type(self) -> None:
        with self.assertRaises(ValidationError):
            create_comment(
                author=self.user,
                target_type="invalid.target",
                target_id=self.event_a.id,
                body="Bad target type",
                parent=None,
            )

    def test_deleted_event_target(self) -> None:
        self.event_a.soft_delete()
        with self.assertRaises(ValidationError):
            create_comment(
                author=self.user,
                target_type="events.event",
                target_id=self.event_a.id,
                body="Comment on deleted event",
                parent=None,
            )

    def test_5000_accepted(self) -> None:
        body = "x" * 5000
        comment = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event_a.id,
            body=body,
            parent=None,
        )
        self.assertEqual(len(comment.body), 5000)

    def test_5001_rejected(self) -> None:
        body = "x" * 5001
        with self.assertRaises(ValidationError):
            create_comment(
                author=self.user,
                target_type="events.event",
                target_id=self.event_a.id,
                body=body,
                parent=None,
            )

    def test_parent_is_set_correctly_at_creation(self) -> None:
        comment = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event_a.id,
            body="Root comment",
            parent=None,
        )
        reply = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event_a.id,
            body="Reply",
            parent=comment,
        )
        reply.refresh_from_db()
        self.assertEqual(reply.parent_id, comment.id)

    def test_arbitrary_deep_chain(self) -> None:
        """Reply-of-reply-of-reply — no nesting limit enforced."""
        c1 = create_comment(
            author=self.user, target_type="events.event",
            target_id=self.event_a.id, body="Level 1", parent=None,
        )
        c2 = create_comment(
            author=self.user, target_type="events.event",
            target_id=self.event_a.id, body="Level 2", parent=c1,
        )
        c3 = create_comment(
            author=self.user, target_type="events.event",
            target_id=self.event_a.id, body="Level 3", parent=c2,
        )
        # All three share the same target
        self.assertEqual(c1.object_id, self.event_a.id)
        self.assertEqual(c2.object_id, self.event_a.id)
        self.assertEqual(c3.object_id, self.event_a.id)
        # Chain integrity: c3→c2→c1
        self.assertEqual(c3.parent_id, c2.id)
        self.assertEqual(c2.parent_id, c1.id)

    def test_soft_delete_behavior(self) -> None:
        comment = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event_a.id,
            body="Will be deleted",
            parent=None,
        )
        soft_delete_comment(comment=comment)
        comment.refresh_from_db()
        self.assertIsNotNone(comment.deleted_at)
        self.assertEqual(comment.body, "")  # or empty string; see service

    def test_create_comment(self) -> None:
        comment = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event_a.id,
            body="A brand new comment",
            parent=None,
        )
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.body, "A brand new comment")
        self.assertIsNone(comment.parent)
        self.assertIsNone(comment.deleted_at)
        # Verify GenericForeignKey resolved correctly
        self.assertEqual(comment.target, self.event_a)
