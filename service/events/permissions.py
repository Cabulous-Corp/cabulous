from rest_framework.permissions import BasePermission


class IsEventCreatorOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.creator_id == request.user.id


class IsStaffOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff
