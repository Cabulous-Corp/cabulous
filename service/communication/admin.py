from django.contrib import admin

from communication.models import DiscordChannel


@admin.register(DiscordChannel)
class DiscordChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "purpose", "is_active", "updated_at")
    list_filter = ("purpose", "is_active")
    search_fields = ("name", "webhook_url")
    ordering = ("purpose", "name")
