from django.contrib.auth.models import BaseUserManager
from django.db import IntegrityError
from loguru import logger

from app.core.exceptions import BaseAPIException, ConflictError


class UserManager(BaseUserManager):
    def _create_user(self, email: str, password: str | None = None, **extra):
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
            elif "phone_number" in str(e):
                raise ConflictError(
                    "User creation failed. User with provided phone number already exists."
                ) from e

            raise ConflictError from e

        except Exception as e:
            logger.error(f"Unhandled error during user creation for '{email}': {e}")
            raise BaseAPIException("User creation failed. Please try again later.")

        return user

    def create_user(self, **extra):
        return self._create_user(**extra)

    def create_superuser(self, **extra):
        extra["user_type"] = "ADMIN"
        extra["is_email_verified"] = True

        return self._create_user(**extra)

    def get_by_natural_key(self, username: str):
        return self.get(email__iexact=username)
