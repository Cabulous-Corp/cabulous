import uuid

from django.db import models


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
