import json

import redis
from celery import shared_task
from django.conf import settings
from loguru import logger

from core.celery import app
from core.tasks.base import BaseTask


@shared_task(base=BaseTask, queue="monitoring")
def redrive_all_from_dlq() -> int:
    client = redis.from_url(settings.CELERY_BROKER_URL)
    count = 0
    while True:
        message = client.lpop("dlq_storage")
        if not message:
            break

        try:
            task_data = json.loads(message)
            task_id = task_data.get("task_id")
            target_queue = task_data.get("original_queue", "default")
            if not target_queue or target_queue == "":
                task_name = task_data.get("task_name", "").lower()

                # Mapping of keywords in task name to their target queues
                queue_map = getattr(
                    settings,
                    "CELERY_TASK_QUEUE_MAP",
                    {
                        "email": "emails",
                        "cache": "caching",
                        "monitoring": "monitoring",
                        "auth": "authentication",
                    },
                )

                target_queue = next(
                    (
                        queue_name
                        for key, queue_name in queue_map.items()
                        if key in task_name
                    ),
                    "default",
                )

            app.send_task(
                task_data.get("task_name"),
                args=task_data.get("args", []),
                kwargs=task_data.get("kwargs", {}),
                queue=target_queue,
            )

            logger.info(
                "Redrove task from DLQ", task_id=task_id, target_queue=target_queue
            )
            count += 1
        except Exception as e:
            logger.error("Failed to redrive message from DLQ", error=str(e))
            client.rpush("dlq_storage", message)
            break

    logger.info("DLQ redrive complete", count=count)
    return count
