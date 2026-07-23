from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsPhotoOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return obj.uploader_id == request.user.id
