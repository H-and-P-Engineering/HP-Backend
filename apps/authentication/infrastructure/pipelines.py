from datetime import UTC, datetime
from typing import Any, Dict

from social_core.pipeline.user import USER_FIELDS

from apps.authentication.domain.events import UserUpdateEvent
from apps.authentication.infrastructure.factory import (
    get_event_publisher,
    get_user_repository,
)
from apps.users.domain.models import User as DomainUser


def create_user(
    backend, details: Dict[str, Any], user: Any = None, *args, **kwargs
) -> Dict[str, Any]:
    user_repository = get_user_repository()
    event_publisher = get_event_publisher()

    if user:
        event_publisher.publish(
            UserUpdateEvent(
                update_fields={"last_login": datetime.now(tz=UTC)},
                user_id=user.id,
            )
        )
        return {"user": user, "is_new": False}

    fields = {
        name: kwargs.get(name, details.get(name))
        for name in backend.setting("USER_FIELDS", USER_FIELDS)
    }

    if not fields:
        return

    fields["is_email_verified"] = True

    domain_user = DomainUser(
        email=fields["email"],
        first_name=fields.get("first_name", ""),
        last_name=fields.get("last_name", ""),
        is_email_verified=fields["is_email_verified"],
    )

    created_user = user_repository.create_social(domain_user)

    event_publisher.publish(
        UserUpdateEvent(
            update_fields={
                "is_email_verified": True,
                "last_login": datetime.now(tz=UTC),
            },
            user_id=created_user.id,
        )
    )

    return {"user": created_user, "is_new": True}
