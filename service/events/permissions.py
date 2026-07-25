from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission


class IsEventCreatorOrStaff(BasePermission):
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        if request.user.is_staff:
            return True
        return obj.creator_id == request.user.id


class IsStaffOnly(BasePermission):
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        return request.user.is_staff
