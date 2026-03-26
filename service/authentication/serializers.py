from typing import Any, cast

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        identifier = attrs["identifier"]
        password = attrs["password"]

        user = authenticate(username=identifier, password=password)
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
            "is_first_login",
            "is_staff",
            "is_active",
        )
        read_only_fields = fields


class RefreshTokenSerializer(TokenRefreshSerializer):
    pass
