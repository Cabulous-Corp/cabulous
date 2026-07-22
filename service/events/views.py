from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.permissions import IsAuthenticatedWithOnboardingGuard
from common.pagination import StandardPageNumberPagination
from events.enums import Audience, EventStatus, EventType
from events.filters import EventFilter
from events.models import Event, EventParticipant, EventPhoto, Highlight
from events.permissions import IsEventCreatorOrStaff, IsStaffOnly
from events.serializers import (
    EventCreateSerializer,
    EventPhotoReadSerializer,
    EventReadSerializer,
    EventUpdateSerializer,
    HighlightReadSerializer,
    HighlightWriteSerializer,
    ParticipantAddSerializer,
    ParticipantReadSerializer,
    PhotoLinkSerializer,
    ThumbnailSerializer,
)
from events.services.events import _UNSET, create_event, update_event
from events.services.highlights import create_highlight, delete_highlight, update_highlight
from events.services.lifecycle import cancel_event, reactivate_event, restore_event
from events.services.relations import (
    add_participants,
    can_unlink,
    link_photo,
    remove_participant,
    set_thumbnail,
    unlink_photo,
)
from media.models import Photo


class EventViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = EventReadSerializer
    permission_classes = [IsAuthenticatedWithOnboardingGuard]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ["title", "description"]
    ordering_fields = ["start_at", "end_at", "created_at", "type", "status"]
    ordering = ["-start_at"]

    def get_queryset(self):
        qs = (
            Event.objects.select_related("creator", "location")
            .prefetch_related("audiences", "participants", "photos__photo")
            .distinct()
        )
        # Hide cancelled events from default list; status filter can still surface them
        if self.action == "list" and "status" not in self.request.query_params:
            qs = qs.exclude(status=EventStatus.CANCELLED)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return EventCreateSerializer
        if self.action in ("update", "partial_update"):
            return EventUpdateSerializer
        return EventReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        event = create_event(
            creator=request.user,
            title=data["title"],
            description=data.get("description", ""),
            start_at=data["start_at"],
            end_at=data["end_at"],
            event_type=data["type"],
            audiences=data["audiences"],
            location=data.get("location"),
        )
        read_serializer = EventReadSerializer(event)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        event = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # location sentinel: not in data = keep, in data with value = replace/remove
        has_location_key = "location" in request.data
        location_payload = data.get("location") if has_location_key else _UNSET

        update_event(
            event=event,
            title=data.get("title"),
            description=data.get("description"),
            start_at=data.get("start_at"),
            end_at=data.get("end_at"),
            event_type=data.get("type"),
            audiences=data.get("audiences"),
            location=location_payload,
        )
        event.refresh_from_db()
        read_serializer = EventReadSerializer(event)
        return Response(read_serializer.data)

    def perform_destroy(self, instance):
        instance.soft_delete()

    def get_permissions(self):
        if self.action in ("options",):
            return [IsAuthenticatedWithOnboardingGuard()]
        if self.action in ("cancel", "reactivate"):
            return [IsAuthenticatedWithOnboardingGuard(), IsEventCreatorOrStaff()]
        if self.action == "restore":
            return [IsAuthenticatedWithOnboardingGuard(), IsStaffOnly()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticatedWithOnboardingGuard(), IsEventCreatorOrStaff()]
        if self.action in ("participants",) and self.request.method == "POST":
            return [IsAuthenticatedWithOnboardingGuard(), IsEventCreatorOrStaff()]
        if self.action == "thumbnail":
            return [IsAuthenticatedWithOnboardingGuard(), IsEventCreatorOrStaff()]
        if self.action in ("highlight_detail",) and self.request.method in ("PATCH", "DELETE"):
            return [IsAuthenticatedWithOnboardingGuard()]
        return [IsAuthenticatedWithOnboardingGuard()]

    @action(detail=False, methods=["get"])
    def options(self, request):
        from events.constants import EVENT_TYPE_COLOR_MAP

        return Response(
            {
                "types": [
                    {
                        "value": value,
                        "label": label,
                        "color": EVENT_TYPE_COLOR_MAP.get(EventType(value), "#FFFFFF"),
                    }
                    for value, label in EventType.choices
                ],
                "audiences": [
                    {"value": value, "label": label}
                    for value, label in Audience.choices
                ],
                "statuses": [
                    {"value": value, "label": label}
                    for value, label in EventStatus.choices
                ],
            }
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        event = self.get_object()
        event = cancel_event(event=event)
        return Response(EventReadSerializer(event).data)

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        event = self.get_object()
        event = reactivate_event(event=event)
        return Response(EventReadSerializer(event).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        try:
            event = Event.all_objects.get_queryset().deleted().get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request, event)
        event = restore_event(event=event)
        return Response(EventReadSerializer(event).data)

    # -------------------------------------------------------------------
    # Participants
    # -------------------------------------------------------------------

    @action(detail=True, methods=["get", "post"], url_path="participants")
    def participants(self, request, pk=None):
        event = self.get_object()
        if request.method == "POST":
            self.check_object_permissions(request, event)
            serializer = ParticipantAddSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            rows = add_participants(
                event=event, user_ids=[str(uid) for uid in serializer.validated_data["user_ids"]]
            )
            return Response(
                ParticipantReadSerializer(rows, many=True).data,
                status=status.HTTP_201_CREATED,
            )
        qs = (
            EventParticipant.objects.filter(event=event)
            .select_related("user")
            .order_by("created_at")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ParticipantReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(ParticipantReadSerializer(qs, many=True).data)

    @action(detail=True, methods=["delete"], url_path=r"participants/(?P<user_id>[^/.]+)")
    def remove_participant(self, request, pk=None, user_id=None):
        event = self.get_object()
        user_id = str(user_id)
        # Creator/staff can remove any; participants can remove themselves
        is_self = str(request.user.id) == user_id
        can_remove = (
            request.user.is_staff
            or str(event.creator_id) == str(request.user.id)
            or is_self
        )
        if not can_remove:
            raise PermissionDenied(
                {"detail": "You do not have permission to remove this participant."}
            )
        remove_participant(event=event, user_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # -------------------------------------------------------------------
    # Photos
    # -------------------------------------------------------------------

    @action(detail=True, methods=["get", "post"], url_path="photos")
    def photos(self, request, pk=None):
        event = self.get_object()
        if request.method == "POST":
            if not (
                request.user.is_staff
                or event.creator_id == request.user.id
                or EventParticipant.objects.filter(
                    event=event, user=request.user
                ).exists()
            ):
                raise PermissionDenied(
                    {"detail": "Only the creator, staff, or participants can link photos."}
                )
            serializer = PhotoLinkSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                photo = Photo.objects.get(id=serializer.validated_data["photo_id"])
            except Photo.DoesNotExist:
                return Response(
                    {"photo_id": "Photo not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            row = link_photo(event=event, photo=photo, user=request.user)
            return Response(
                EventPhotoReadSerializer(row).data,
                status=status.HTTP_201_CREATED,
            )
        qs = EventPhoto.objects.filter(event=event).select_related("photo").order_by("created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = EventPhotoReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(EventPhotoReadSerializer(qs, many=True).data)

    @action(detail=True, methods=["delete"], url_path=r"photos/(?P<photo_pk>[^/.]+)")
    def unlink_photo(self, request, pk=None, photo_pk=None):
        event = self.get_object()
        if not can_unlink(event=event, photo_id=photo_pk, user=request.user):
            raise PermissionDenied(
                {"detail": "You do not have permission to unlink this photo."}
            )
        unlink_photo(event=event, photo_id=photo_pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # -------------------------------------------------------------------
    # Thumbnail
    # -------------------------------------------------------------------

    @action(detail=True, methods=["put", "delete"], url_path="thumbnail")
    def thumbnail(self, request, pk=None):
        event = self.get_object()
        self.check_object_permissions(request, event)
        if request.method == "DELETE":
            set_thumbnail(event=event, photo=None)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = ThumbnailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            photo = Photo.objects.get(id=serializer.validated_data["photo_id"])
        except Photo.DoesNotExist:
            return Response(
                {"photo_id": "Photo not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        row = set_thumbnail(event=event, photo=photo)
        return Response(EventPhotoReadSerializer(row).data, status=status.HTTP_200_OK)

    # -------------------------------------------------------------------
    # Highlights
    # -------------------------------------------------------------------

    def _get_event_and_highlight(self, request, pk, highlight_pk):
        """Fetch event and highlight, scoped by event_id."""
        event = self.get_object()
        try:
            highlight = (
                Highlight.objects.select_related("author")
                .prefetch_related("photos__photo")
                .get(id=highlight_pk, event=event)
            )
        except Highlight.DoesNotExist:
            return event, None
        return event, highlight

    @action(detail=True, methods=["get", "post"], url_path="highlights")
    def highlights(self, request, pk=None):
        event = self.get_object()

        if request.method == "POST":
            # creator/staff/participant can create
            is_participant = (
                request.user.is_staff
                or event.creator_id == request.user.id
                or EventParticipant.objects.filter(event=event, user=request.user).exists()
            )
            if not is_participant:
                raise PermissionDenied(
                    {"detail": "Only the creator, staff, or participants can create highlights."}
                )
            serializer = HighlightWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            hl = create_highlight(
                event=event,
                author=request.user,
                text=data["text"],
                photo_ids=data.get("photo_ids", []),
            )
            return Response(
                HighlightReadSerializer(hl).data, status=status.HTTP_201_CREATED
            )

        # GET - list
        qs = Highlight.objects.filter(event=event).prefetch_related(
            "photos__photo"
        ).order_by("created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = HighlightReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(HighlightReadSerializer(qs, many=True).data)

    @action(
        detail=True,
        methods=["get", "patch", "delete"],
        url_path=r"highlights/(?P<highlight_pk>[^/.]+)",
    )
    def highlight_detail(self, request, pk=None, highlight_pk=None):
        event, highlight = self._get_event_and_highlight(request, pk, highlight_pk)
        if highlight is None:
            return Response(
                {"detail": "Highlight not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "GET":
            return Response(HighlightReadSerializer(highlight).data)

        if request.method == "DELETE":
            # creator/staff can delete any; author can delete own
            if not (
                request.user.is_staff
                or event.creator_id == request.user.id
                or highlight.author_id == request.user.id
            ):
                raise PermissionDenied(
                    {"detail": "You do not have permission to delete this highlight."}
                )
            delete_highlight(highlight=highlight)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # PATCH
        # creator/staff can edit any; author can edit own
        if not (
            request.user.is_staff
            or event.creator_id == request.user.id
            or highlight.author_id == request.user.id
        ):
            raise PermissionDenied(
                {"detail": "You do not have permission to edit this highlight."}
            )

        serializer = HighlightWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        update_highlight(
            highlight=highlight,
            text=data.get("text"),
            photo_ids=data.get("photo_ids"),
        )

        highlight.refresh_from_db()
        return Response(HighlightReadSerializer(highlight).data)
