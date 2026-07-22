import os
from typing import Any

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cabulous.settings")

app = Celery("cabulous")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self: Any) -> None:
    print(f"Request: {self.request!r}")
