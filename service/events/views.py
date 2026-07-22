from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.permissions import IsAuthenticatedWithOnboardingGuard
from common.pagination import StandardPageNumberPagination
from events.enums import Audience, EventStatus, EventType
from events.filters import EventFilter
from events.models import Event
from events.permissions import IsEventCreatorOrStaff, IsStaffOnly
from events.serializers import EventCreateSerializer, EventReadSerializer, EventUpdateSerializer
from events.services.events import _UNSET, create_event, update_event
from events.services.lifecycle import cancel_event, reactivate_event, restore_event


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
