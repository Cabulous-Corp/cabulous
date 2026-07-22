from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/communication/", include("communication.urls")),
    path("api/integrations/", include("integrations.urls")),
    path("api/monitoring/", include("monitoring.urls")),
    path("api/users/", include("users.urls")),
]
