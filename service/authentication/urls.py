from django.urls import path

from authentication.views import (
    ForgotAccessView,
    LoginView,
    LogoutView,
    MeView,
    OnboardingFirstAccessView,
    PasswordResetConfirmView,
    RefreshView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("forgot-password/", ForgotAccessView.as_view(), name="auth-forgot-password"),
    path(
        "reset-password/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-reset-password-confirm",
    ),
    path(
        "onboarding/complete/",
        OnboardingFirstAccessView.as_view(),
        name="auth-onboarding-complete",
    ),
]
