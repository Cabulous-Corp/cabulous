from celery import shared_task


@shared_task
def healthcheck_task() -> str:
    return "ok"
