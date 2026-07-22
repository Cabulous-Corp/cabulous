import uuid

from django.db import models
from django.utils import timezone


class AbstractDatableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AbstractUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(AbstractUUIDModel, AbstractDatableModel):
    class Meta(AbstractUUIDModel.Meta, AbstractDatableModel.Meta):
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def active(self) -> "SoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=True)

    def deleted(self) -> "SoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=False)

    def delete(self) -> tuple[int, dict[str, int]]:
        updated_count = self.active().update(deleted_at=timezone.now())
        return updated_count, {self.model._meta.label: updated_count}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()


class AbstractSoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(
        verbose_name="Excluído em",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def _soft_delete_update_fields(self) -> list[str]:
        fields = ["deleted_at"]
        if hasattr(self, "updated_at"):
            fields.append("updated_at")
        return fields

    def soft_delete(self) -> None:
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=self._soft_delete_update_fields())

    def restore(self) -> None:
        if self.deleted_at is not None:
            self.deleted_at = None
            self.save(update_fields=self._soft_delete_update_fields())

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def delete(
        self, using: str | None = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        self.soft_delete()
        return 1, {self._meta.label: 1}
