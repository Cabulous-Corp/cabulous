import django_filters

from events.models import Event


class EventFilter(django_filters.FilterSet):
    starts_from = django_filters.DateFilter(field_name="start_at", lookup_expr="date__gte")
    starts_until = django_filters.DateFilter(field_name="start_at", lookup_expr="date__lte")
    status = django_filters.ChoiceFilter(choices=[], field_name="status")
    type = django_filters.ChoiceFilter(choices=[], field_name="type")
    audience = django_filters.ChoiceFilter(choices=[], method="filter_by_audience")
    participant = django_filters.UUIDFilter(method="filter_by_participant")
    creator = django_filters.UUIDFilter(field_name="creator_id")

    class Meta:
        model = Event
        fields = [
            "starts_from",
            "starts_until",
            "status",
            "type",
            "audience",
            "participant",
            "creator",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from events.enums import Audience, EventStatus, EventType

        self.filters["status"].extra["choices"] = EventStatus.choices
        self.filters["type"].extra["choices"] = EventType.choices
        self.filters["audience"].extra["choices"] = Audience.choices

    def filter_by_audience(self, queryset, name, value):
        return queryset.filter(audiences__audience=value).distinct()

    def filter_by_participant(self, queryset, name, value):
        return queryset.filter(participants__user_id=value).distinct()
