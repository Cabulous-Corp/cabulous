from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

ALLOWED_PENDING_ONBOARDING_URL_NAMES = {
    "auth-login",
    "auth-refresh",
    "auth-logout",
    "auth-me",
    "auth-onboarding-complete",
}


class IsAuthenticatedWithOnboardingGuard(BasePermission):
    # DRF uses this default message when has_permission returns False
    # without raising a custom exception.
    message = "Authentication credentials were not provided."

    def has_permission(self, request: object, view: object) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False

        if getattr(user, "is_superuser", False):
            return True

        if getattr(user, "onboarding_completed_at", None) is not None:
            return True

        if getattr(view, "allow_pending_onboarding", False):
            return True

        resolver_match = getattr(request, "resolver_match", None)
        url_name = getattr(resolver_match, "url_name", None)
        if url_name in ALLOWED_PENDING_ONBOARDING_URL_NAMES:
            return True

        raise PermissionDenied(
            detail={
                "code": "onboarding_required",
                "detail": "Complete onboarding before accessing this endpoint.",
            }
        )
