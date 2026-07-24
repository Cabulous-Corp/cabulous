from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from comments.services import create_comment, soft_delete_comment
from events.enums import EventStatus, EventType
from events.models import Event
from users.models import User


def _create_user(username: str = "user1", **overrides: object) -> User:
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
    return Event.objects.create(**defaults)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class CommentListTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("user1")
        self.event = _create_event(self.user)
        self.url = "/api/comments/"

    def test_requires_target_type_and_target_id(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("target_type", resp.data)  # type: ignore[attr-defined]
        self.assertIn("target_id", resp.data)  # type: ignore[attr-defined]

    def test_rejects_invalid_target_type(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        resp = self.client.get(self.url, {"target_type": "invalid", "target_id": self.event.id})  # type: ignore[arg-type]
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("target_type", resp.data)  # type: ignore[attr-defined]

    def test_returns_comments_paginated_20(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        for i in range(25):
            create_comment(
                author=self.user,
                target_type="events.event",
                target_id=self.event.id,
                body=f"Comment {i + 1}",
                parent=None,
            )
        params = {"target_type": "events.event", "target_id": self.event.id}
        resp = self.client.get(self.url, params)  # type: ignore[arg-type]
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 20)  # type: ignore[attr-defined]
        self.assertIsNotNone(resp.data["next"])  # type: ignore[attr-defined]

    def test_deterministic_chronological_order(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        # Create comments with known ordering
        c1 = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="First",
            parent=None,
        )
        c2 = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="Second",
            parent=None,
        )
        create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="Third",
            parent=None,
        )
        params = {"target_type": "events.event", "target_id": self.event.id}
        resp = self.client.get(self.url, params)  # type: ignore[arg-type]
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data["results"]  # type: ignore[attr-defined]
        # c1 and c2 may share same created_at; stable ordering by id within created_at
        ids = [r["id"] for r in results]
        expected = [str(c1.id), str(c2.id)]
        # First two should be c1, c2 in that order since created_at, id
        self.assertEqual(ids[:2], expected)

    def test_arbitrary_depth_no_recursive_serialization(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        c1 = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="Level 1",
            parent=None,
        )
        c2 = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="Level 2",
            parent=c1,
        )
        create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="Level 3",
            parent=c2,
        )
        params = {"target_type": "events.event", "target_id": self.event.id}
        resp = self.client.get(self.url, params)  # type: ignore[arg-type]
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # All comments are flat in the same list, with parent_id indicating structure
        for item in resp.data["results"]:  # type: ignore[attr-defined]
            self.assertIn("id", item)
            self.assertIn("parent_id", item)
            self.assertIn("body", item)
            self.assertIn("author_id", item)
            self.assertNotIn("replies", item)

    def test_excludes_comments_on_deleted_event_target(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        event2 = _create_event(self.user, title="Deleted Event")
        create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="On active event",
            parent=None,
        )
        create_comment(
            author=self.user,
            target_type="events.event",
            target_id=event2.id,
            body="On to-be-deleted event",
            parent=None,
        )
        # Delete event2
        event2.soft_delete()
        params = {"target_type": "events.event", "target_id": self.event.id}
        resp = self.client.get(self.url, params)  # type: ignore[arg-type]
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)  # type: ignore[attr-defined]
        self.assertEqual(resp.data["results"][0]["body"], "On active event")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class CommentCreateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("user1")
        self.event = _create_event(self.user)
        self.url = "/api/comments/"

    def test_create_comment_successfully(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        resp = self.client.post(
            self.url,
            {
                "target_type": "events.event",
                "target_id": str(self.event.id),
                "body": "Great event!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["body"], "Great event!")  # type: ignore[attr-defined]
        self.assertEqual(resp.data["author_id"], str(self.user.id))  # type: ignore[attr-defined]
        self.assertIsNone(resp.data["parent_id"])  # type: ignore[attr-defined]

    def test_create_with_parent(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        parent = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="Parent",
            parent=None,
        )
        resp = self.client.post(
            self.url,
            {
                "target_type": "events.event",
                "target_id": str(self.event.id),
                "body": "Reply",
                "parent_id": str(parent.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["parent_id"], str(parent.id))  # type: ignore[attr-defined]

    def test_create_invalid_target_type(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        resp = self.client.post(
            self.url,
            {
                "target_type": "invalid.target",
                "target_id": str(self.event.id),
                "body": "Bad target",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_parent(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        resp = self.client.post(
            self.url,
            {
                "target_type": "events.event",
                "target_id": str(self.event.id),
                "body": "Bad parent",
                "parent_id": "00000000-0000-0000-0000-000000000000",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_deleted_target_returns_404(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        self.event.soft_delete()
        resp = self.client.post(
            self.url,
            {
                "target_type": "events.event",
                "target_id": str(self.event.id),
                "body": "On deleted event",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_anonymous_returns_401(self) -> None:
        resp = self.client.post(
            self.url,
            {"target_type": "events.event", "target_id": str(self.event.id), "body": "Anon"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_pending_onboarding_returns_403(self) -> None:
        user = _create_user("pending", onboarding_completed_at=None)
        self.client.force_authenticate(user)  # type: ignore[attr-defined]
        resp = self.client.post(
            self.url,
            {"target_type": "events.event", "target_id": str(self.event.id), "body": "Pending"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Retrieve
# ---------------------------------------------------------------------------


class CommentRetrieveTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = _create_user("user1")
        self.event = _create_event(self.user)
        self.comment = create_comment(
            author=self.user,
            target_type="events.event",
            target_id=self.event.id,
            body="Read me",
            parent=None,
        )
        self.url = f"/api/comments/{self.comment.id}/"

    def test_retrieve_comment(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], str(self.comment.id))  # type: ignore[attr-defined]
        self.assertEqual(resp.data["body"], "Read me")  # type: ignore[attr-defined]
        self.assertEqual(resp.data["author_id"], str(self.user.id))  # type: ignore[attr-defined]
        self.assertEqual(resp.data["target_type"], "events.event")  # type: ignore[attr-defined]
        self.assertEqual(resp.data["target_id"], str(self.event.id))  # type: ignore[attr-defined]
        self.assertFalse(resp.data["is_deleted"])  # type: ignore[attr-defined]

    def test_soft_deleted_returns_body_null_and_is_deleted_true(self) -> None:
        self.client.force_authenticate(self.user)  # type: ignore[attr-defined]
        soft_delete_comment(comment=self.comment)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["body"])  # type: ignore[attr-defined]
        self.assertTrue(resp.data["is_deleted"])  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Update (PATCH)
# ---------------------------------------------------------------------------


class CommentUpdateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = _create_user("author")
        self.other = _create_user("other")
        self.event = _create_event(self.author)
        self.comment = create_comment(
            author=self.author,
            target_type="events.event",
            target_id=self.event.id,
            body="Original body",
            parent=None,
        )
        self.url = f"/api/comments/{self.comment.id}/"

    def test_author_can_update_body(self) -> None:
        self.client.force_authenticate(self.author)  # type: ignore[attr-defined]
        resp = self.client.patch(self.url, {"body": "Updated body"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["body"], "Updated body")  # type: ignore[attr-defined]

    def test_non_author_cannot_update_returns_403(self) -> None:
        self.client.force_authenticate(self.other)  # type: ignore[attr-defined]
        resp = self.client.patch(self.url, {"body": "Hacked"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Delete (Destroy)
# ---------------------------------------------------------------------------


class CommentDeleteTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = _create_user("author")
        self.other = _create_user("other")
        self.event = _create_event(self.author)
        self.comment = create_comment(
            author=self.author,
            target_type="events.event",
            target_id=self.event.id,
            body="Delete me",
            parent=None,
        )
        self.url = f"/api/comments/{self.comment.id}/"

    def test_author_can_soft_delete_returns_204(self) -> None:
        self.client.force_authenticate(self.author)  # type: ignore[attr-defined]
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.comment.refresh_from_db()
        self.assertIsNotNone(self.comment.deleted_at)

    def test_non_author_cannot_delete_returns_403(self) -> None:
        self.client.force_authenticate(self.other)  # type: ignore[attr-defined]
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_delete_returns_401(self) -> None:
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_does_not_cascade_to_children(self) -> None:
        self.client.force_authenticate(self.author)  # type: ignore[attr-defined]
        reply = create_comment(
            author=self.author,
            target_type="events.event",
            target_id=self.event.id,
            body="Reply",
            parent=self.comment,
        )
        # Soft-delete parent
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        # Reply still exists
        reply.refresh_from_db()
        self.assertIsNone(reply.deleted_at)
        self.assertEqual(reply.body, "Reply")


# ---------------------------------------------------------------------------
# Permissions: Staff and Event Creator
# ---------------------------------------------------------------------------


class CommentStaffModerationTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.staff = _create_user("staff", is_staff=True)
        self.author = _create_user("author")
        self.event = _create_event(_create_user("event_creator"))
        self.comment = create_comment(
            author=self.author,
            target_type="events.event",
            target_id=self.event.id,
            body="Staff can moderate",
            parent=None,
        )
        self.url = f"/api/comments/{self.comment.id}/"

    def test_staff_can_delete_any_comment(self) -> None:
        self.client.force_authenticate(self.staff)  # type: ignore[attr-defined]
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_staff_can_update_any_comment(self) -> None:
        self.client.force_authenticate(self.staff)  # type: ignore[attr-defined]
        resp = self.client.patch(self.url, {"body": "Staff edited"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_event_creator_without_staff_cannot_moderate_others_comments(self) -> None:
        event_creator = _create_user("event_creator_2")
        # Re-create event with this user as creator
        event = _create_event(event_creator)
        comment = create_comment(
            author=self.author,
            target_type="events.event",
            target_id=event.id,
            body="On event creator's event",
            parent=None,
        )
        url = f"/api/comments/{comment.id}/"
        self.client.force_authenticate(event_creator)  # type: ignore[attr-defined]
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp2 = self.client.patch(url, {"body": "Mod by event creator"}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)
