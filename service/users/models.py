import uuid
from pathlib import Path
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from common.models.abstracts import BaseModel
from users.validators import (
    normalize_discord_username,
    normalize_phone_number,
    normalize_username,
    validate_discord_username_format,
    validate_phone_number_format,
    validate_username_format,
)


def user_media_base_path(instance: models.Model) -> str:
    user_uuid = getattr(instance, "uuid", None) or uuid.uuid4()
    return f"users/{user_uuid}"


def user_avatar_upload_to(instance: models.Model, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{user_media_base_path(instance)}/avatar{suffix}"


def user_banner_upload_to(instance: models.Model, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{user_media_base_path(instance)}/banner{suffix}"


class User(BaseModel, AbstractUser):
    username = models.CharField(
        verbose_name="Nome de usuário",
        max_length=150,
        unique=True,
        validators=[validate_username_format],
    )
    email = models.EmailField(
        verbose_name="E-mail",
        unique=True,
        blank=False,
    )
    discord_username = models.CharField(
        verbose_name="Usuário do Discord",
        max_length=100,
        blank=True,
        default="",
        validators=[validate_discord_username_format],
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

    class Meta(BaseModel.Meta):
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        indexes = [
            models.Index(fields=["discord_username"], name="users_discord_idx"),
            models.Index(fields=["phone_number"], name="users_phone_idx"),
        ]
        constraints = [
            models.UniqueConstraint(Lower("username"), name="users_username_ci_unique"),
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
