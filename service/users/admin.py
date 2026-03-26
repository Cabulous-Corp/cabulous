from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User, UserMagicLinkToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "invited_at",
        "invitation_accepted_at",
        "password_defined_at",
        "onboarding_completed_at",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "discord_username",
        "phone_number",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        ("invited_at", admin.EmptyFieldListFilter),
        ("invitation_accepted_at", admin.EmptyFieldListFilter),
        ("password_defined_at", admin.EmptyFieldListFilter),
        ("onboarding_completed_at", admin.EmptyFieldListFilter),
    )
    ordering = ("username",)
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = ("created_at", "updated_at", "date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações Pessoais", {"fields": ("first_name", "last_name", "email")}),
        (
            "Perfil",
            {
                "fields": (
                    "discord_username",
                    "phone_number",
                    "bio",
                    "avatar",
                    "banner",
                )
            },
        ),
        (
            "Jornada",
            {
                "fields": (
                    "invited_at",
                    "invitation_accepted_at",
                    "password_defined_at",
                    "onboarding_completed_at",
                )
            },
        ),
        (
            "Permissões",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Datas Importantes",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )


@admin.register(UserMagicLinkToken)
class UserMagicLinkTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_by", "expires_at", "used_at", "created_at")
    search_fields = ("user__username", "user__email", "token")
    list_filter = (
        ("used_at", admin.EmptyFieldListFilter),
        ("expires_at", admin.DateFieldListFilter),
        ("created_at", admin.DateFieldListFilter),
    )
    readonly_fields = ("token", "created_at", "updated_at")
