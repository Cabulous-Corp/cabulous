from typing import Any, cast

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.serializers import (
    ForgotAccessSerializer,
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    OnboardingFirstAccessSerializer,
    PasswordResetConfirmSerializer,
    RefreshTokenSerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = cast(dict[str, Any], serializer.validated_data)
        user = validated_data["user"]

        token = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(token.access_token),
                "refresh": str(token),
                "user": MeSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = RefreshTokenSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    allow_pending_onboarding = True

    def get(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = MeSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ForgotAccessView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = ForgotAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "detail": (
                    "If an account exists for the provided identifier, "
                    "recovery instructions were sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password reset completed successfully."},
            status=status.HTTP_200_OK,
        )


class OnboardingFirstAccessView(APIView):
    permission_classes = [IsAuthenticated]
    allow_pending_onboarding = True

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        user = request.user
        if user.onboarding_completed_at is not None:
            return Response(
                {"detail": "Onboarding has already been completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OnboardingFirstAccessSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            MeSerializer(user, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
