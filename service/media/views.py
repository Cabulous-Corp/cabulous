from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from authentication.permissions import IsAuthenticatedWithOnboardingGuard
from common.pagination import StandardPageNumberPagination
from media.filters import PhotoFilter
from media.models import Photo
from media.permissions import IsPhotoOwnerOrStaff
from media.serializers import (
    PhotoConfirmRequestSerializer,
    PhotoSerializer,
    PhotoUploadUrlsRequestSerializer,
)
from media.services.deletion import hard_delete_photo
from media.services.upload_signing import confirm_upload, generate_photo_upload_signed_url


class PhotoUploadUrlsView(APIView):
    permission_classes = [IsAuthenticatedWithOnboardingGuard]

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = PhotoUploadUrlsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        files_data = serializer.validated_data["files"]

        results = []
        for file_data in files_data:
            try:
                result = generate_photo_upload_signed_url(
                    user_id=str(request.user.id),
                    filename=file_data["filename"],
                    content_type=file_data["content_type"],
                )
            except DjangoValidationError as exc:
                raise ValidationError(exc.messages) from exc
            results.append(result)

        return Response({"photos": results}, status=status.HTTP_200_OK)


class PhotoConfirmView(APIView):
    permission_classes = [IsAuthenticatedWithOnboardingGuard]

    def post(self, request: Any, *_args: Any, **_kwargs: Any) -> Response:
        serializer = PhotoConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            photos = confirm_upload(
                user=request.user,
                photos_data=serializer.validated_data["files"],
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc

        return Response(
            PhotoSerializer(photos, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class PhotoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticatedWithOnboardingGuard, IsPhotoOwnerOrStaff]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = PhotoFilter
    search_fields = ["caption"]

    def get_queryset(self):
        return Photo.objects.all()

    def perform_destroy(self, instance: Photo) -> None:
        hard_delete_photo(photo=instance)
