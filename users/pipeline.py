from asgiref.sync import async_to_sync
from typing import Any

from social_core.pipeline.user import USER_FIELDS

from .repositories import user_repository


def create_user(
    backend, details: dict[str, Any], user: Any = None, *args, **kwargs
) -> dict[str, Any]:
    if user:
        return {"user": user, "is_new": False}

    user_type = kwargs.get("user_type")

    fields = {
        name: kwargs.get(name, details.get(name))
        for name in backend.setting("USER_FIELDS", USER_FIELDS)
    }

    if not fields:
        return

    fields["is_email_verified"] = True
    fields["user_type"] = user_type

    created_user = async_to_sync(user_repository.create)(**fields)

    return {"user": created_user, "is_new": True}
