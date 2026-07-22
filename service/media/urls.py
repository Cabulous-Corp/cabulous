from django.urls import include, path
from rest_framework.routers import DefaultRouter

from media.views import PhotoConfirmView, PhotoUploadUrlsView, PhotoViewSet

router = DefaultRouter()
router.register("photos", PhotoViewSet, basename="photo")

urlpatterns = [
    path("photos/upload-urls/", PhotoUploadUrlsView.as_view(), name="photo-upload-urls"),
    path("photos/confirm/", PhotoConfirmView.as_view(), name="photo-confirm"),
    *router.urls,
]
