import uuid
from pathlib import Path
from typing import Any

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from common.models.abstracts import AbstractSoftDeleteModel, BaseModel, SoftDeleteQuerySet
from users.validators import (
    normalize_discord_username,
    normalize_phone_number,
    normalize_username,
    validate_discord_username_format,
    validate_phone_number_format,
    validate_username_format,
)


class ActiveUserManager(UserManager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class AllUserManager(UserManager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


def user_media_base_path(instance: models.Model) -> str:
    user_uuid = getattr(instance, "uuid", None) or uuid.uuid4()
    return f"users/{user_uuid}"


def user_avatar_upload_to(instance: models.Model, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{user_media_base_path(instance)}/avatar{suffix}"


def user_banner_upload_to(instance: models.Model, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{user_media_base_path(instance)}/banner{suffix}"


class User(AbstractSoftDeleteModel, BaseModel, AbstractUser):
    username = models.CharField(
        verbose_name="Nome de usuário",
        max_length=150,
        unique=True,
        validators=[validate_username_format],
    )
    email = models.EmailField(
        verbose_name="E-mail",
        blank=False,
    )
    discord_username = models.CharField(
        verbose_name="Usuário do Discord",
        max_length=100,
        blank=True,
        unique=True,
        default=None,
        validators=[validate_discord_username_format],
    )
    git_username = models.CharField(
        verbose_name="Usuário do GitHub",
        max_length=100,
        blank=True,
        unique=True,
        default=None,
    )
    phone_number = models.CharField(
        verbose_name="Número de telefone",
        max_length=20,
        blank=True,
        default="",
        validators=[validate_phone_number_format],
    )
    avatar = models.ImageField(
        verbose_name="Avatar",
        upload_to=user_avatar_upload_to,
        blank=True,
        null=True,
    )
    banner = models.ImageField(
        verbose_name="Banner",
        upload_to=user_banner_upload_to,
        blank=True,
        null=True,
    )
    bio = models.TextField(
        verbose_name="Bio",
        blank=True,
        default="",
    )
    onboarding_completed_at = models.DateTimeField(
        verbose_name="Onboarding concluído em",
        null=True,
        blank=True,
    )
    password_defined_at = models.DateTimeField(
        verbose_name="Senha definida em",
        null=True,
        blank=True,
    )
    invited_at = models.DateTimeField(
        verbose_name="Convidado em",
        null=True,
        blank=True,
    )
    invitation_accepted_at = models.DateTimeField(
        verbose_name="Convite aceito em",
        null=True,
        blank=True,
    )

    objects = ActiveUserManager()  # type: ignore[misc]
    all_objects = AllUserManager()

    class Meta(BaseModel.Meta):
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        indexes = [
            models.Index(fields=["phone_number"], name="users_phone_idx"),
        ]
        constraints = [
            models.UniqueConstraint(Lower("username"), name="users_username_ci_unique"),
            models.UniqueConstraint(
                Lower("email"),
                condition=Q(deleted_at__isnull=True),
                name="users_email_ci_unique",
            ),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self) -> str:
        return self.username

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.username = normalize_username(self.username)
        self.discord_username = normalize_discord_username(self.discord_username)
        self.phone_number = normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)

    def _deleted_username(self) -> str:
        suffix = f"deleted-{uuid.uuid4().hex[:8]}"
        max_base_length = 150 - len(suffix) - 1
        base_username = self.username[:max_base_length]
        return f"{base_username}-{suffix}"

    def _deleted_email(self) -> str:
        suffix = uuid.uuid4().hex[:8]
        if "@" not in self.email:
            return f"deleted-{suffix}-{self.email or 'unknown'}@cabulous.local"

        local_part, domain = self.email.split("@", 1)
        trimmed_local = local_part[: max(1, 64 - len(suffix) - len("deleted-") - 1)]
        return f"{trimmed_local}+deleted-{suffix}@{domain}"

    def soft_delete(self) -> None:
        if self.deleted_at is not None:
            return

        self.username = self._deleted_username()
        self.email = self._deleted_email()
        self.is_active = False
        self.save(update_fields=["username", "email", "is_active"])
        super().soft_delete()


class UserMagicLinkToken(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="magic_link_tokens",
        verbose_name="Usuário",
    )
    token = models.CharField(
        verbose_name="Token",
        max_length=128,
        unique=True,
    )
    expires_at = models.DateTimeField(
        verbose_name="Expira em",
    )
    used_at = models.DateTimeField(
        verbose_name="Usado em",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_magic_link_tokens",
        verbose_name="Criado por",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Token de link mágico"
        verbose_name_plural = "Tokens de link mágico"
        indexes = [
            models.Index(fields=["token"], name="users_magic_token_idx"),
            models.Index(fields=["expires_at"], name="users_magic_expires_idx"),
            models.Index(fields=["used_at"], name="users_magic_used_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.token[:10]}..."
