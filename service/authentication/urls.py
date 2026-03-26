from django.urls import path

from authentication.views import (
    LoginView,
    LogoutView,
    MeView,
    OnboardingFirstAccessView,
    RefreshView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path(
        "onboarding/complete/",
        OnboardingFirstAccessView.as_view(),
        name="auth-onboarding-complete",
    ),
]
