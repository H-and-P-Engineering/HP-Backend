from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.utils import timezone
from social_core.pipeline.user import USER_FIELDS

from core.infrastructure.exceptions import BadRequestError

User = get_user_model()


def create_user(
    backend, details: Dict[str, Any], user=None, *args, **kwargs
) -> Dict[str, Any]:
    if user:
        if not user.is_email_verified:
            raise BadRequestError(
                detail="Requested user email is not verified. Please verify your email"
            )

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

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
    user = User.objects.create_user(**fields)

    return {"user": user, "is_new": True}
