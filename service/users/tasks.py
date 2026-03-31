from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from users.models import UserMagicLinkToken


@shared_task
def cleanup_magic_links() -> str:
    deleted_count, _ = UserMagicLinkToken.objects.filter(
        Q(expires_at__lte=timezone.now()) | Q(used_at__isnull=False)
    ).delete()
    return f"{deleted_count} magic links deleted"
