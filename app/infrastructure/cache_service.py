from typing import Any

from django.conf import settings
from django.core.cache import cache


class DjangoCacheService:
    def get(self, key: str) -> Any:
        return cache.get(key, None)

    def set(
        self, key: str, value: Any, timeout: int | None = settings.DJANGO_CACHE_TIMEOUT
    ) -> None:
        cache.set(key, value, timeout)

    def delete(self, key: str) -> None:
        try:
            cache.delete(key)
        except:
            pass
