from celery import shared_task


@shared_task
def monitoring_task() -> str:
    return "monitoring ok"
