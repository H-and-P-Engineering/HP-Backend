from typing import Any

from celery import shared_task
from django.core.cache import cache

from .base import BaseTask


@shared_task(base=BaseTask, queue="caching")
def set_cache_task(key: str, value: Any, timeout: int | None = None) -> None:
    cache.set(key, value, timeout)


@shared_task(base=BaseTask, queue="caching")
def delete_cache_task(key: str) -> None:
    cache.delete(key)
