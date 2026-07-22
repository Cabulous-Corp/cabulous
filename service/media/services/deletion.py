from django.core.files.storage import default_storage

from common.exceptions import ServiceUnavailable
from media.models import Photo


def hard_delete_photo(*, photo: Photo) -> None:
    storage = default_storage
    key = photo.object_key
    try:
        storage.delete(key)
    except Exception:
        raise ServiceUnavailable("Failed to delete file from storage.")
    photo.delete()
