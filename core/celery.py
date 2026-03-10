import os

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

from core.logging import setup_logging as core_setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("hp-ecosystem")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args, **kwargs):
    core_setup_logging(log_level=settings.LOGGING_LEVEL, log_file=settings.LOG_FILE)
