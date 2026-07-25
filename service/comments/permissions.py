from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission


class CommentPermission(BasePermission):
    """Object-level permission for comments.

    - Staff can moderate any comment.
    - Comment author can edit/delete their own comment.
    - Event creator without staff role cannot moderate others' comments.
    """

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        # PATCH / DELETE — only author or staff
        if request.user.is_staff:
            return True
        return obj.author_id == request.user.id
