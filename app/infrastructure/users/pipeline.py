from typing import Any, Dict

from social_core.pipeline.user import USER_FIELDS

from app.domain.users.entities import User as DomainUser

from .repositories import DjangoUserRepository


def create_user(
    backend, details: Dict[str, Any], user: Any = None, *args, **kwargs
) -> Dict[str, Any]:
    user_repository = DjangoUserRepository()

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

    domain_user = DomainUser(
        email=fields["email"],
        first_name=fields.get("first_name", ""),
        last_name=fields.get("last_name", ""),
        is_email_verified=fields["is_email_verified"],
    )

    created_user = user_repository.create_social_user(domain_user)

    return {"user": created_user, "is_new": True}
