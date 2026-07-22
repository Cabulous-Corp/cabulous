from django.core.exceptions import ValidationError
from django.db.models import Model

from events.models import Event

ALLOWED_TARGETS: dict[str, type[Model]] = {"events.event": Event}


def resolve_target_model(target_type: str) -> type[Model]:
    model = ALLOWED_TARGETS.get(target_type)
    if model is None:
        raise ValidationError({"target_type": "Unsupported comment target type."})
    return model
