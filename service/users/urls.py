from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views import UserUploadSignedUrlView, UserViewSet

router = DefaultRouter()
router.register("", UserViewSet, basename="users")

urlpatterns = [
    path("uploads/signed-url/", UserUploadSignedUrlView.as_view(), name="users-upload-signed-url"),
    *router.urls,
]
