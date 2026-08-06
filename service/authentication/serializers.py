import secrets
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from cabulous.config import get_settings
from communication.tasks import (
    send_discord_channel_message_by_purpose_task,
    send_html_template_email_task,
)
from users.models import UserMagicLinkToken
from users.validators import (
    clean_discord_username,
    clean_phone_number,
    clean_username,
    normalize_username,
    validate_object_key,
)

if TYPE_CHECKING:
    from users.models import User as UserType

    User = UserType
else:
    User = get_user_model()
app_settings = get_settings()


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        identifier = attrs["identifier"]
        password = attrs["password"]

        user = authenticate(username=normalize_username(identifier), password=password)
        if user is None:
            user_from_email = User.objects.filter(email__iexact=identifier).first()
            if user_from_email is not None:
                user = authenticate(username=user_from_email.username, password=password)

        if user is None:
            raise AuthenticationFailed("Invalid credentials.")

        if not user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs: Any) -> dict[str, Any]:
        validated_data = cast(dict[str, Any], self.validated_data)
        refresh_token = validated_data["refresh"]

        token = RefreshToken(refresh_token)
        token.blacklist()
        return {}


class MeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "avatar",
            "banner",
            "onboarding_completed_at",
            "password_defined_at",
            "invited_at",
            "invitation_accepted_at",
            "is_staff",
            "is_active",
        )
        read_only_fields = fields


def _send_recovery(
    user: "UserType",
    *,
    subject: str,
    template_path: str,
    context: dict[str, Any],
    content: str,
) -> None:
    if user.email:
        send_html_template_email_task.delay(
            subject=subject,
            recipients=[user.email],
            template_path=template_path,
            context=context,
        )
    if user.discord_username:
        send_discord_channel_message_by_purpose_task.delay(
            purpose="BOARD_UPDATES",
            content=content,
        )


class ForgotAccessSerializer(serializers.Serializer):
    identifier = serializers.CharField(trim_whitespace=True)

    def save(self, **kwargs: Any) -> dict[str, Any]:
        validated_data = cast(dict[str, Any], self.validated_data)
        identifier = validated_data["identifier"]

        user = User.objects.filter(username=normalize_username(identifier)).first()
        if user is None:
            user = User.objects.filter(email__iexact=identifier).first()

        if user is None or not user.is_active:
            return {}

        frontend_url = app_settings.app_frontend_url.rstrip("/")
        display_name = user.first_name or user.username

        if user.onboarding_completed_at is None:
            return self._send_pending_onboarding_recovery(user, frontend_url, display_name)
        return self._send_password_reset_recovery(user, frontend_url, display_name)

    @staticmethod
    def _send_pending_onboarding_recovery(
        user: "UserType", frontend_url: str, display_name: str
    ) -> dict[str, Any]:
        magic_token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=72)
        UserMagicLinkToken.objects.create(
            user=user,
            token=magic_token,
            expires_at=expires_at,
            created_by=None,
        )
        onboarding_link = f"{frontend_url}/magic-login/{magic_token}"
        onboarding_context = {
            "display_name": display_name,
            "magic_link": onboarding_link,
            "magic_link_expires_at_display": timezone.localtime(expires_at).strftime(
                "%d/%m/%Y %H:%M"
            ),
        }
        _send_recovery(
            user,
            subject="Recuperacao de acesso - Cabulous",
            template_path="email/authentication/recover_pending_onboarding.html",
            context=onboarding_context,
            content=(
                f"{user.discord_username}, voce possui onboarding pendente no Cabulous. "
                f"Use este link para concluir o primeiro acesso: {onboarding_link}"
            ),
        )
        return {}

    @staticmethod
    def _send_password_reset_recovery(
        user: "UserType", frontend_url: str, display_name: str
    ) -> dict[str, Any]:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"
        reset_context = {
            "display_name": display_name,
            "reset_link": reset_link,
        }
        _send_recovery(
            user,
            subject="Redefinicao de senha - Cabulous",
            template_path="email/authentication/password_reset_request.html",
            context=reset_context,
            content=(
                f"{user.discord_username}, recebemos uma solicitacao de redefinicao de senha "
                f"para sua conta Cabulous. Use este link: {reset_link}"
            ),
        )
        return {}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        uid = attrs["uid"]
        token = attrs["token"]
        new_password = attrs["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError({"token": "Invalid reset token."}) from exc

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid or expired reset token."})

        validate_password(new_password, user=user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs: Any) -> dict[str, Any]:
        validated_data = cast(dict[str, Any], self.validated_data)
        user = validated_data["user"]
        new_password = validated_data["new_password"]

        user.set_password(new_password)
        user.password_defined_at = timezone.now()
        user.save()
        return {}


class OnboardingFirstAccessSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    avatar_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    banner_key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "new_password",
            "email",
            "username",
            "first_name",
            "last_name",
            "discord_username",
            "phone_number",
            "avatar",
            "avatar_key",
            "banner",
            "banner_key",
            "bio",
        )
        extra_kwargs: dict[str, dict[str, Any]] = {
            "username": {"validators": []},
            "avatar": {"read_only": True},
            "banner": {"read_only": True},
        }

    def validate_new_password(self, value: str) -> str:
        user = self.instance
        validate_password(value, user=user)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if self.initial_data.get("avatar"):
            raise serializers.ValidationError(
                {"avatar": "Direct file upload is not allowed. Use avatar_key from signed upload."}
            )
        if self.initial_data.get("banner"):
            raise serializers.ValidationError(
                {"banner": "Direct file upload is not allowed. Use banner_key from signed upload."}
            )
        if "new_password" not in attrs:
            raise serializers.ValidationError({"new_password": "This field is required."})
        return attrs

    def validate_username(self, value: str) -> str:
        instance_pk = self.instance.pk if self.instance is not None else None
        try:
            return clean_username(value, queryset=User.objects.all(), exclude_pk=instance_pk)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_discord_username(self, value: str) -> str:
        try:
            return clean_discord_username(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_phone_number(self, value: str) -> str:
        try:
            return clean_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_avatar_key(self, value: str) -> str:
        try:
            return validate_object_key(value, self.instance, "avatar")
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_banner_key(self, value: str) -> str:
        try:
            return validate_object_key(value, self.instance, "banner")
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def update(self, instance: "UserType", validated_data: dict[str, Any]) -> "UserType":
        password = validated_data.pop("new_password", None)
        avatar_key = validated_data.pop("avatar_key", "")
        banner_key = validated_data.pop("banner_key", "")
        if password is None:
            raise serializers.ValidationError({"new_password": "This field is required."})

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.set_password(password)

        now = timezone.now()
        instance.password_defined_at = now
        instance.onboarding_completed_at = now
        if instance.invitation_accepted_at is None:
            instance.invitation_accepted_at = now

        if avatar_key:
            instance.avatar = avatar_key
        if banner_key:
            instance.banner = banner_key

        instance.save()
        return instance
