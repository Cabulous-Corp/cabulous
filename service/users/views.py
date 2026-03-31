from typing import Any, cast

from django.utils import timezone
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from authentication.permissions import IsAuthenticatedWithOnboardingGuard
from cabulous.config import get_settings
from communication.tasks import send_html_template_email_task
from users.models import User
from users.permissions import UserModelPermissions
from users.serializers import UserSerializer

app_settings = get_settings()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedWithOnboardingGuard, UserModelPermissions]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        user_serializer = cast(UserSerializer, serializer)
        user = user_serializer.save()
        invite_payload = user_serializer.get_invite_access_payload()

        if not user.email or invite_payload is None:
            return

        invite_display_name = user.first_name or user.username
        context: dict[str, Any] = {
            "invite_display_name": invite_display_name,
            "temporary_password": invite_payload["temporary_password"],
            "magic_link": invite_payload["magic_link"],
            "magic_link_expires_at_display": timezone.localtime(
                invite_payload["magic_link_expires_at"]
            ).strftime("%d/%m/%Y %H:%M"),
            "login_url": f"{app_settings.app_frontend_url.rstrip('/')}/login",
        }

        send_html_template_email_task.delay(
            subject="Seu convite para acessar o Cabulous",
            recipients=[user.email],
            template_path="email/users/invite_access.html",
            context=context,
        )
