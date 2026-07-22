from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from .models import Comment
from .targets import resolve_target_model


class CommentCreateSerializer(serializers.Serializer):
    target_type = serializers.CharField()
    target_id = serializers.UUIDField()
    body = serializers.CharField(max_length=5000)
    parent_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    def validate_parent_id(self, parent_id):
        if parent_id is None:
            return None
        try:
            Comment.objects.get(id=parent_id)
        except Comment.DoesNotExist:
            raise serializers.ValidationError("Comment not found.")
        return parent_id

    def validate(self, data):
        target_type = data["target_type"]
        target_id = data["target_id"]
        parent_id = data.get("parent_id")

        # Validate target_type is allowed
        model_cls = resolve_target_model(target_type)

        # Validate target exists (and is not soft-deleted)
        try:
            model_cls.objects.get(pk=target_id)
        except model_cls.DoesNotExist:
            raise NotFound("Target not found.")

        # Validate parent belongs to same target if provided
        if parent_id is not None:
            target_ct = ContentType.objects.get_for_model(model_cls)
            try:
                parent = Comment.objects.get(id=parent_id)
            except Comment.DoesNotExist:
                raise serializers.ValidationError({"parent_id": "Comment not found."})
            if parent.content_type_id != target_ct.id or parent.object_id != target_id:
                raise serializers.ValidationError(
                    {"parent_id": "Parent comment must share the same target."}
                )

        return data


class CommentReadSerializer(serializers.ModelSerializer):
    author_id = serializers.UUIDField(source="author.id", read_only=True)
    author_name = serializers.CharField(source="author.username", read_only=True)
    parent_id = serializers.UUIDField(read_only=True, default=None)
    target_type = serializers.SerializerMethodField()
    target_id = serializers.UUIDField(source="object_id", read_only=True)
    is_deleted = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author_id",
            "author_name",
            "body",
            "parent_id",
            "target_type",
            "target_id",
            "created_at",
            "updated_at",
            "is_deleted",
        ]

    def get_target_type(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def get_is_deleted(self, obj):
        return obj.deleted_at is not None

    def get_body(self, obj):
        if obj.deleted_at is not None:
            return None
        return obj.body


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["body"]

    def update(self, instance, validated_data):
        instance.body = validated_data["body"]
        instance.save(update_fields=["body", "updated_at"])
        return instance
