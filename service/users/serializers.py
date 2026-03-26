from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from users.models import User

SELF_EDITABLE_FIELDS = {
    "username",
    "email",
    "first_name",
    "last_name",
    "bio",
    "phone_number",
    "discord_username",
    "avatar",
    "banner",
}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "discord_username",
            "phone_number",
            "avatar",
            "banner",
            "bio",
            "onboarding_completed_at",
            "password_defined_at",
            "invited_at",
            "invitation_accepted_at",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "last_login",
            "date_joined",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "last_login",
            "date_joined",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        view = self.context.get("view")
        action = getattr(view, "action", None)

        if request is None or action is None:
            return attrs

        if action in {"update", "partial_update"}:
            if request.user.has_perm("users.change_user"):
                return attrs

            if self.instance is None or self.instance.pk != request.user.pk:
                raise PermissionDenied("You can only edit your own account.")

            disallowed_fields = set(attrs.keys()) - SELF_EDITABLE_FIELDS
            if disallowed_fields:
                raise PermissionDenied(
                    "You do not have permission to edit these fields: "
                    + ", ".join(sorted(disallowed_fields))
                )

        return attrs
