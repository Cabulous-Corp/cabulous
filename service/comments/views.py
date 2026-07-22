from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.permissions import IsAuthenticatedWithOnboardingGuard
from common.pagination import StandardPageNumberPagination
from events.models import Event

from .models import Comment
from .permissions import CommentPermission
from .serializers import (
    CommentCreateSerializer,
    CommentReadSerializer,
    CommentUpdateSerializer,
)
from .services import create_comment, soft_delete_comment
from .targets import resolve_target_model


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = CommentReadSerializer
    permission_classes = [IsAuthenticatedWithOnboardingGuard, CommentPermission]
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        return (
            Comment.objects.select_related("author", "content_type")
            .order_by("created_at", "id")
        )

    def _get_filtered_queryset(self):
        """List requires target_type and target_id query params."""
        qs = self.get_queryset()
        # Exclude comments on deleted Event targets
        event_ct = ContentType.objects.get_for_model(Event)
        active_event_ids = Event.objects.values_list("id", flat=True)
        qs = qs.exclude(
            Q(content_type=event_ct) & ~Q(object_id__in=active_event_ids)
        )
        return qs

    def list(self, request, *args, **kwargs):
        target_type = request.query_params.get("target_type")
        target_id = request.query_params.get("target_id")

        if not target_type or not target_id:
            return Response(
                {
                    "target_type": ["This field is required."],
                    "target_id": ["This field is required."],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate target_type against registry
        try:
            resolve_target_model(target_type)
        except DjangoValidationError:
            return Response(
                {"target_type": ["Unsupported comment target type."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self._get_filtered_queryset()
        model_cls = resolve_target_model(target_type)
        target_ct = ContentType.objects.get_for_model(model_cls)
        qs = qs.filter(content_type=target_ct, object_id=target_id)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = CommentReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CommentReadSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        parent_id = data.get("parent_id")
        parent = Comment.objects.get(id=parent_id) if parent_id else None
        comment = create_comment(
            author=request.user,
            target_type=data["target_type"],
            target_id=data["target_id"],
            body=data["body"],
            parent=parent,
        )
        read_serializer = CommentReadSerializer(comment)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        soft_delete_comment(comment=instance)

    def get_serializer_class(self):
        if self.action == "create":
            return CommentCreateSerializer
        if self.action in ("update", "partial_update"):
            return CommentUpdateSerializer
        return CommentReadSerializer
