from django.urls import path

from monitoring.views import healthcheck

urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
]
