from django.contrib import admin
from django.db import transaction

from .models import (
    Event,
    EventAudience,
    EventLocation,
    EventParticipant,
    EventPhoto,
    Highlight,
    HighlightPhoto,
)
from .services.lifecycle import restore_event


class EventAudienceInline(admin.TabularInline):
    model = EventAudience
    extra = 1


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 0
    autocomplete_fields = ["user"]


class EventLocationInline(admin.StackedInline):
    model = EventLocation
    extra = 0
    max_num = 1


class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 0
    autocomplete_fields = ["photo"]


class HighlightInline(admin.TabularInline):
    model = Highlight
    extra = 0
    autocomplete_fields = ["author"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "creator", "type", "status", "start_at", "deleted_at"]
    list_filter = ["status", "type", "deleted_at"]
    search_fields = ["title", "description"]
    autocomplete_fields = ["creator"]
    inlines = [
        EventAudienceInline,
        EventParticipantInline,
        EventLocationInline,
        EventPhotoInline,
        HighlightInline,
    ]

    def get_queryset(self, request):
        return Event.all_objects.select_related("creator")

    @admin.action(description="Restore selected events")
    def restore_event_action(self, request, queryset):
        restored = 0
        with transaction.atomic():
            for event in queryset:
                restore_event(event=event)
                restored += 1
        self.message_user(request, f"{restored} event(s) restored.")

    actions = [restore_event_action]


@admin.register(EventAudience)
class EventAudienceAdmin(admin.ModelAdmin):
    list_display = ["event", "audience"]
    list_filter = ["audience"]
    autocomplete_fields = ["event"]


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ["event", "user"]
    autocomplete_fields = ["event", "user"]


@admin.register(EventLocation)
class EventLocationAdmin(admin.ModelAdmin):
    list_display = ["event", "name", "address"]
    autocomplete_fields = ["event"]


@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ["event", "photo", "is_thumbnail"]
    autocomplete_fields = ["event", "photo"]


@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ["event", "text", "author"]
    search_fields = ["text"]
    autocomplete_fields = ["event", "author"]


@admin.register(HighlightPhoto)
class HighlightPhotoAdmin(admin.ModelAdmin):
    list_display = ["highlight", "photo"]
    autocomplete_fields = ["highlight", "photo"]
