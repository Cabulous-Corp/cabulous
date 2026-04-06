from typing import Any, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from authentication.permissions import IsAuthenticatedWithOnboardingGuard
from cabulous.config import get_settings
from communication.tasks import send_html_template_email_task
from users.models import User
from users.permissions import UserModelPermissions
from users.serializers import UserSerializer, UserUploadSignedUrlRequestSerializer
from users.services.upload_signing import generate_upload_signed_url

app_settings = get_settings()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedWithOnboardingGuard, UserModelPermissions]

    def perform_destroy(self, instance: User) -> None:
        instance.soft_delete()

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


class UserUploadSignedUrlView(APIView):
    permission_classes = [IsAuthenticatedWithOnboardingGuard]
    allow_pending_onboarding = True

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = UserUploadSignedUrlRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)

        target_user = self._resolve_target_user(request.user, validated_data.get("target_user_id"))
        try:
            signed_payload = generate_upload_signed_url(
                user=target_user,
                file_type=validated_data["file_type"],
                filename=validated_data["filename"],
                content_type=validated_data["content_type"],
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return Response(signed_payload, status=status.HTTP_200_OK)

    @staticmethod
    def _resolve_target_user(request_user: User, target_user_id: Any | None) -> User:
        if target_user_id is None:
            return request_user

        if str(request_user.id) == str(target_user_id):
            return request_user

        if request_user.has_perm("users.change_user"):
            return get_object_or_404(User, id=target_user_id)

        raise PermissionDenied(
            "You do not have permission to generate upload URLs for other users."
        )
