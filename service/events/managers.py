from django.db import models

from common.models.abstracts import SoftDeleteQuerySet


class ActiveEventManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class AllEventManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted(self) -> SoftDeleteQuerySet:
        return self.get_queryset().deleted()

    def active(self) -> SoftDeleteQuerySet:
        return self.get_queryset().active()
