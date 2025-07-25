from typing import TYPE_CHECKING

from django.contrib.auth.models import BaseUserManager
from django.db import IntegrityError

from core.infrastructure.exceptions.base import BaseAPIException, ConflictError
from core.infrastructure.logging.base import logger

if TYPE_CHECKING:
    from apps.users.infrastructure.models import User


class UserManager(BaseUserManager):
    def _create_user(self, email: str, password: str | None = None, **extra) -> "User":
        normalized_email = self.normalize_email(email)
        user = self.model(email=normalized_email, **extra)

        if extra.get("is_superuser", False):
            user.set_password(password)
        else:
            user.password = password

        if not password:
            user.set_unusable_password()

        try:
            user.save(using=self._db)
        except IntegrityError as e:
            if "email" in str(e):
                raise ConflictError(
                    "User creation failed. User with provided email already exists."
                ) from e
            elif "unique_phone_number_constraint" in str(e):
                raise ConflictError(
                    "User creation failed. User with provided phone number already exists."
                ) from e

            logger.error(f"Integrity error during user creation for '{email}': {e}")
            raise ConflictError from e

        except Exception as e:
            logger.critical(f"Unhandled error during user creation for '{email}': {e}")
            raise BaseAPIException("User creation failed. Please try again later.")

        return user

    def create_user(self, **extra) -> "User":
        return self._create_user(**extra)

    def create_superuser(self, **extra) -> "User":
        extra["user_type"] = "ADMIN"
        extra["is_email_verified"] = True

        return self._create_user(**extra)

    def get_by_natural_key(self, username: str) -> "User":
        return self.get(email__iexact=username)
