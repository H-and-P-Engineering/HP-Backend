import json
import os
import redis
import traceback
from datetime import datetime
from typing import Any

from celery import Task
from django.conf import settings
from loguru import logger
from uuid6 import UUID

from monitoring.models import FailedTask


def json_serializer(obj: Any) -> str:
    if isinstance(obj, (datetime, UUID)):
        return str(obj)
    return str(obj)  # Fallback to string for everything else (e.g. coroutines)


class BaseTask(Task):
    autoretry_for = (Exception,)
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    retry_backoff = True
    retry_backoff_max = settings.CELERY_TASK_RETRY_BACKOFF_MAX
    retry_jitter = True

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        logger.error(
            "Task failed",
            task_name=self.name,
            task_id=task_id,
            error=str(exc),
            args=args,
        )

        original_queue = (
            self.request.delivery_info.get("routing_key")
            if self.request.delivery_info
            else "default"
        )

        try:
            while isinstance(task_id, str) and task_id.startswith("dlq-"):
                task_id = task_id[4:]

            FailedTask.objects.update_or_create(
                task_id=task_id,
                defaults={
                    "task_name": self.name,
                    "args": json.dumps(args, default=json_serializer),
                    "kwargs": json.dumps(kwargs, default=json_serializer),
                    "exception": exc,
                    "traceback": traceback.format_exc(),
                    "queue": original_queue,
                },
            )
            logger.info("Logged failed task to database", task_id=task_id)
        except Exception as e:
            logger.error(
                "Failed to log task to database", task_id=task_id, error=str(e)
            )

        try:
            client = redis.from_url(os.getenv("CELERY_BROKER_URL"))
            dlq_entry = json.dumps(
                {
                    "task_id": task_id,
                    "task_name": self.name,
                    "args": args,
                    "kwargs": kwargs,
                    "original_queue": original_queue,
                    "error": str(exc),
                }
            )
            client.rpush("dlq_storage", dlq_entry)
            logger.info("Moved task to Redis DLQ", task_id=task_id)
        except Exception as e:
            logger.error(
                "Failed to move task to Redis DLQ", task_id=task_id, error=str(e)
            )

        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        logger.warning(
            "Retrying task", task_name=self.name, task_id=task_id, error=str(exc)
        )

        try:
            while isinstance(task_id, str) and task_id.startswith("dlq-"):
                task_id = task_id[4:]

            FailedTask.objects.update_or_create(
                task_id=task_id,
                defaults={
                    "task_name": self.name,
                    "args": json.dumps(args, default=json_serializer),
                    "kwargs": json.dumps(kwargs, default=json_serializer),
                    "exception": f"RETRYING: {exc}",
                    "traceback": traceback.format_exc(),
                },
            )
        except Exception as e:
            logger.error("Failed to log retry for task", task_id=task_id, error=str(e))

        super().on_retry(exc, task_id, args, kwargs, einfo)
