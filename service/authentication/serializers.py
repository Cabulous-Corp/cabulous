from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from users.validators import (
    clean_discord_username,
    clean_phone_number,
    clean_username,
    normalize_username,
)

User = get_user_model()

if TYPE_CHECKING:
    from users.models import User as UserType


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

    def save(self, **kwargs) -> dict:
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


class RefreshTokenSerializer(TokenRefreshSerializer):
    pass


class OnboardingFirstAccessSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

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
            "bio",
        )
        extra_kwargs = {
            "username": {"validators": []},
        }

    def validate_new_password(self, value: str) -> str:
        user = self.instance
        validate_password(value, user=user)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
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

    def update(self, instance: "UserType", validated_data: dict[str, Any]) -> "UserType":
        password = validated_data.pop("new_password", None)
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

        instance.save()
        return instance
