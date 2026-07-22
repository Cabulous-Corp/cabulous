from django.contrib import admin

from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ["object_key", "uploader", "taken_on", "content_type", "size_bytes"]
    list_filter = ["content_type"]
    search_fields = ["object_key", "uploader__username"]
    readonly_fields = ["created_at", "updated_at", "object_key"]
    autocomplete_fields = ["uploader"]
