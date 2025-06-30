from typing import TYPE_CHECKING

from django.contrib.auth.models import BaseUserManager
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from apps.authentication.infrastructure.models import User

from core.infrastructure.exceptions import BaseAPIException, ConflictError
from core.infrastructure.logging.base import logger


class UserManager(BaseUserManager):
    def _create_user(self, email: str, password: str | None = None, **extra) -> "User":
        email = self.normalize_email(email)

        user = self.model(email=email, **extra)

        if extra.get("is_superuser", False) == True:
            user.set_password(password)
        else:
            user.password = password

        if not password:
            user.set_unusable_password()

        try:
            user.save(using=self._db)
        except IntegrityError as e:
            if "email" in str(e):
                raise ConflictError(_("User with this email already exists.")) from e

            logger.exception(
                f"Integrity error during user creation for '{email}': {e}."
            )
            raise ConflictError("User creation failed. Conflicting resource exists.") from e
        except Exception as e:
            logger.exception(f"Unknown error during user creation for '{email}': {e}")
            raise BaseAPIException(_("User creation failed. Try again later.")) from e

        return user

    def create_user(self, **extra) -> "User":
        if extra.get("user_type") == "ADMIN":
            raise ValueError(
                "The user_type 'ADMIN' is not available for regular users."
            )

        return self._create_user(**extra)

    def create_superuser(self, **extra) -> "User":
        extra.setdefault("user_type", "ADMIN")
        extra.setdefault("is_email_verified", True)

        return self._create_user(**extra)

    def get_by_natural_key(self, username: str) -> "User":
        return self.get(email__iexact=username)
