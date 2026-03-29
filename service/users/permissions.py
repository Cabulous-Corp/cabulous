from rest_framework.permissions import DjangoModelPermissions


class UserModelPermissions(DjangoModelPermissions):
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    def has_permission(self, request, view):
        action = getattr(view, "action", "")
        if action in {"list", "retrieve"}:
            return bool(request.user and request.user.is_authenticated)
        if action in {"update", "partial_update"} and request.user.is_authenticated:
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        action = getattr(view, "action", "")
        if action in {"update", "partial_update"}:
            if request.user.has_perm("users.change_user"):
                return True
            return obj.pk == request.user.pk
        return True
