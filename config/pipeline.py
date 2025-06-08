from typing import Any

from django.utils.translation import gettext_lazy as _
from social_core.pipeline.user import USER_FIELDS

from core.exceptions import BadRequestError


def create_user(
    backend, details: dict[str, Any], user=None, *args, **kwargs
) -> dict[str, Any]:
    """Custom pipeline to create social user."""

    if user:
        if not user.is_email_verified:
            raise BadRequestError(
                _("Requested user email is not verified. Please verify your email")
            )

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

    user = backend.strategy.create_user(**fields)

    return {"user": user, "is_new": True}
