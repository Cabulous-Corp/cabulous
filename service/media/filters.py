from __future__ import annotations

import django_filters
from django.db.models import QuerySet

from media.models import Photo


class PhotoFilter(django_filters.FilterSet):
    taken_from = django_filters.DateFilter(field_name="taken_on", lookup_expr="gte")
    taken_until = django_filters.DateFilter(field_name="taken_on", lookup_expr="lte")
    uploader = django_filters.UUIDFilter(field_name="uploader_id")
    event = django_filters.UUIDFilter(method="filter_by_event")

    class Meta:
        model = Photo
        fields = ["taken_from", "taken_until", "uploader", "event"]

    def filter_by_event(self, queryset: QuerySet, _name: str, value: str) -> QuerySet:
        return queryset.filter(event_photos__event_id=value)
