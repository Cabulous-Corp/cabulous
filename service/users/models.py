import uuid
from pathlib import Path

from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models.abstracts import BaseModel


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
    )
    phone_number = models.CharField(
        verbose_name="Número de telefone",
        max_length=20,
        blank=True,
        default="",
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

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self) -> str:
        return self.username
