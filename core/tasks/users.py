import asyncio
from datetime import datetime, UTC

from celery import shared_task
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import (
    TokenError,
    ExpiredTokenError,
    InvalidToken,
)
from uuid6 import UUID

from .base import BaseTask
from core.container import container
from users.models import User


@shared_task(base=BaseTask, queue="users")
def update_user_data_task(user_uuid: UUID, data: dict) -> None:
    user = User.objects.get(uuid=user_uuid)
    for key, value in data.items():
        setattr(user, key, value)

    user.save(update_fields=data.keys())


@shared_task(base=BaseTask, queue="users")
def invalidate_previous_session_task(user_id: int) -> None:
    cache = container.active_token_cache_service()
    active_token = cache.get_active_token(user_id)

    if active_token:
        try:
            token_obj = AccessToken(active_token)
            expires_at = datetime.fromtimestamp(token_obj.get("exp"), tz=UTC)

            asyncio.run(
                container.blacklisted_token_repository().create(
                    access=token_obj, user_id=user_id, expires_at=expires_at
                )
            )
        except (TokenError, ExpiredTokenError, InvalidToken):
            pass

        cache.delete_active_token(user_id)
