import os
import pickle

from celery import Celery, shared_task

from .events import EventBus

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("hp-clean")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@shared_task
def publish_event_to_bus(event_data: bytes) -> None:
    event = pickle.loads(event_data)
    EventBus.publish(event)
