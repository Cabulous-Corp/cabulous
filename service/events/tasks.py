from celery import shared_task

from events.models import Event
from events.services.lifecycle import reconcile_event_status


@shared_task
def reconcile_event_statuses() -> int:
    updated_count = 0
    # Use iterator with chunk size to avoid loading all IDs into memory
    event_ids = list(
        Event.objects.filter(deleted_at__isnull=True)
        .values_list("id", flat=True)
        .iterator(chunk_size=500)
    )

    for i in range(0, len(event_ids), 500):
        chunk_ids = event_ids[i : i + 500]
        events = Event.objects.filter(id__in=chunk_ids, deleted_at__isnull=True)
        for event in events:
            old_status = event.status
            reconcile_event_status(event=event)
            if event.status != old_status:
                updated_count += 1

    return updated_count
