from django.urls import path

from core.views import healthcheck

urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
]
