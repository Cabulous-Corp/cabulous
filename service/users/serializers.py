import secrets
import string
from datetime import timedelta
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from cabulous.config import get_settings
from users.models import User, UserMagicLinkToken
from users.services.upload_signing import UPLOAD_FILE_TYPES
from users.validators import clean_discord_username, clean_phone_number, clean_username

SELF_EDITABLE_FIELDS = {
    "username",
    "email",
    "first_name",
    "last_name",
    "bio",
    "phone_number",
    "discord_username",
    "avatar_key",
    "banner_key",
}

app_settings = get_settings()


class UserSerializer(serializers.ModelSerializer):
    _invite_access_payload: dict[str, Any] | None = None
    avatar_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    banner_key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "discord_username",
            "phone_number",
            "avatar",
            "avatar_key",
            "banner",
            "banner_key",
            "bio",
            "onboarding_completed_at",
            "password_defined_at",
            "invited_at",
            "invitation_accepted_at",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "last_login",
            "date_joined",
            "created_at",
            "updated_at",
            "deleted_at",
        )
        read_only_fields = (
            "id",
            "last_login",
            "date_joined",
            "created_at",
            "updated_at",
            "deleted_at",
        )
        extra_kwargs = {
            "username": {"validators": []},
            "avatar": {"read_only": True},
            "banner": {"read_only": True},
        }

    def validate(self, attrs: dict) -> dict:
        if self.initial_data.get("avatar"):
            raise serializers.ValidationError(
                {"avatar": "Direct file upload is not allowed. Use avatar_key from signed upload."}
            )
        if self.initial_data.get("banner"):
            raise serializers.ValidationError(
                {"banner": "Direct file upload is not allowed in this endpoint."}
            )

        request = self.context.get("request")
        view = self.context.get("view")
        action = getattr(view, "action", None)

        if request is None or action is None:
            return attrs

        if action in {"update", "partial_update"}:
            if request.user.has_perm("users.change_user"):
                return attrs

            if self.instance is None or self.instance.pk != request.user.pk:
                raise PermissionDenied("You can only edit your own account.")

            disallowed_fields = set(attrs.keys()) - SELF_EDITABLE_FIELDS
            if disallowed_fields:
                raise PermissionDenied(
                    "You do not have permission to edit these fields: "
                    + ", ".join(sorted(disallowed_fields))
                )

        return attrs

    def validate_username(self, value: str) -> str:
        instance_pk = self.instance.pk if self.instance is not None else None
        try:
            return clean_username(
                value,
                queryset=User.objects.all(),
                exclude_pk=instance_pk,
            )
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
        if not value:
            return ""

        target_user = self.instance
        if target_user is None:
            raise serializers.ValidationError(
                "Avatar upload is not supported during user creation."
            )

        expected_prefix = f"users/{target_user.id}/avatar/"
        if not value.startswith(expected_prefix):
            raise serializers.ValidationError("Invalid avatar object key for this user.")
        if not default_storage.exists(value):
            raise serializers.ValidationError("Uploaded avatar object was not found.")
        return value

    def validate_banner_key(self, value: str) -> str:
        if not value:
            return ""

        target_user = self.instance
        if target_user is None:
            raise serializers.ValidationError(
                "Banner upload is not supported during user creation."
            )

        expected_prefix = f"users/{target_user.id}/banner/"
        if not value.startswith(expected_prefix):
            raise serializers.ValidationError("Invalid banner object key for this user.")
        if not default_storage.exists(value):
            raise serializers.ValidationError("Uploaded banner object was not found.")
        return value

    def create(self, validated_data: dict) -> User:
        request = self.context.get("request")
        groups = validated_data.pop("groups", [])
        user_permissions = validated_data.pop("user_permissions", [])
        avatar_key = validated_data.pop("avatar_key", "")
        banner_key = validated_data.pop("banner_key", "")

        if avatar_key or banner_key:
            raise serializers.ValidationError(
                {
                    "avatar_key": "Media upload is not supported during user creation.",
                    "banner_key": "Media upload is not supported during user creation.",
                }
            )

        temporary_password = self._generate_temporary_password()
        user = User(**validated_data)
        user.set_password(temporary_password)
        user.invited_at = timezone.now()
        user.save()
        if groups:
            user.groups.set(groups)
        if user_permissions:
            user.user_permissions.set(user_permissions)

        magic_token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=72)

        created_by = None
        if request is not None and request.user.is_authenticated:
            created_by = request.user

        UserMagicLinkToken.objects.create(
            user=user,
            token=magic_token,
            expires_at=expires_at,
            created_by=created_by,
        )

        frontend_url = app_settings.app_frontend_url.rstrip("/")
        magic_link = f"{frontend_url}/magic-login/{magic_token}"
        self._invite_access_payload = {
            "temporary_password": temporary_password,
            "magic_link": magic_link,
            "magic_link_expires_at": expires_at,
        }

        return user

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        avatar_key = validated_data.pop("avatar_key", "")
        banner_key = validated_data.pop("banner_key", "")
        user = super().update(instance, validated_data)
        updated_fields: list[str] = []
        if avatar_key:
            user.avatar = avatar_key
            updated_fields.append("avatar")
        if banner_key:
            user.banner = banner_key
            updated_fields.append("banner")
        if updated_fields:
            user.save(update_fields=[*updated_fields, "updated_at"])
        return user

    def get_invite_access_payload(self) -> dict[str, Any] | None:
        payload = getattr(self, "_invite_access_payload", None)
        if payload is None:
            return None
        return dict(payload)

    @staticmethod
    def _generate_temporary_password(length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        return "".join(secrets.choice(alphabet) for _ in range(length))


class UserUploadSignedUrlRequestSerializer(serializers.Serializer):
    file_type = serializers.ChoiceField(choices=sorted(UPLOAD_FILE_TYPES))
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=255)
    target_user_id = serializers.UUIDField(required=False)
