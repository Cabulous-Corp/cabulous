from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "author", "content_type", "object_id", "created_at", "deleted_at"]
    search_fields = ["author__username", "body"]
    list_filter = ["content_type"]
