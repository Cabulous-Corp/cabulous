import secrets
import string
from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from cabulous.config import get_settings
from users.models import User, UserMagicLinkToken
from users.validators import clean_username

SELF_EDITABLE_FIELDS = {
    "username",
    "email",
    "first_name",
    "last_name",
    "bio",
    "phone_number",
    "discord_username",
    "avatar",
    "banner",
}

app_settings = get_settings()


class UserSerializer(serializers.ModelSerializer):
    temporary_password = serializers.SerializerMethodField()
    magic_link = serializers.SerializerMethodField()
    magic_link_expires_at = serializers.SerializerMethodField()

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
            "banner",
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
            "temporary_password",
            "magic_link",
            "magic_link_expires_at",
        )
        read_only_fields = (
            "id",
            "last_login",
            "date_joined",
            "created_at",
            "updated_at",
            "temporary_password",
            "magic_link",
            "magic_link_expires_at",
        )
        extra_kwargs = {
            "username": {"validators": []},
        }

    def validate(self, attrs: dict) -> dict:
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
            return clean_username(value, queryset=User.objects.all(), exclude_pk=instance_pk)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    def create(self, validated_data: dict) -> User:
        request = self.context.get("request")
        groups = validated_data.pop("groups", [])
        user_permissions = validated_data.pop("user_permissions", [])

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
        user._temporary_password = temporary_password  # type: ignore[attr-defined]
        user._magic_link = f"{frontend_url}/magic-login/{magic_token}"  # type: ignore[attr-defined]
        user._magic_link_expires_at = expires_at  # type: ignore[attr-defined]

        return user

    def get_temporary_password(self, obj: User) -> str | None:
        return getattr(obj, "_temporary_password", None)

    def get_magic_link(self, obj: User) -> str | None:
        return getattr(obj, "_magic_link", None)

    def get_magic_link_expires_at(self, obj: User):
        return getattr(obj, "_magic_link_expires_at", None)

    def to_representation(self, instance: User) -> dict:
        data = super().to_representation(instance)
        for key in ("temporary_password", "magic_link", "magic_link_expires_at"):
            if data.get(key) is None:
                data.pop(key, None)
        return data

    @staticmethod
    def _generate_temporary_password(length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        return "".join(secrets.choice(alphabet) for _ in range(length))
