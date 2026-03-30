from rest_framework.permissions import DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.views import APIView


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

    def has_permission(self, request: Request, view: APIView) -> bool:
        request_user = request.user
        action = getattr(view, "action", "")
        if action in {"list", "retrieve"}:
            return bool(request_user and getattr(request_user, "is_authenticated", False))
        if action in {"update", "partial_update"} and getattr(
            request_user, "is_authenticated", False
        ):
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        request_user = request.user
        action = getattr(view, "action", "")
        if action in {"update", "partial_update"}:
            if request_user and getattr(request_user, "has_perm", lambda _perm: False)(
                "users.change_user"
            ):
                return True
            return getattr(obj, "pk", None) == getattr(request_user, "pk", None)
        return True
