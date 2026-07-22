import logging

from django.core.files.storage import default_storage

from common.exceptions import ServiceUnavailable
from media.models import Photo

logger = logging.getLogger(__name__)


def hard_delete_photo(*, photo: Photo) -> None:
    storage = default_storage
    key = photo.object_key
    try:
        storage.delete(key)
    except Exception as exc:
        logger.exception("Storage delete failed for %s", key)
        raise ServiceUnavailable(detail=f"Storage delete failed: {exc}") from exc
    photo.delete()
