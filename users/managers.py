from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import BaseUserManager
from django.db import IntegrityError
from loguru import logger

from core.exceptions import BaseAPIException, ConflictError

if TYPE_CHECKING:
    from .models import User


class UserManager(BaseUserManager):
    def _prepare_user(
        self, email: str, password: str | None = None, **extra: Any
    ) -> User:
        normalized_email = self.normalize_email(email)
        user: User = self.model(email=normalized_email, **extra)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        return user

    def _handle_integrity_error(self, exc: IntegrityError) -> None:
        if "email" in str(exc):
            raise ConflictError(
                "User creation failed. User with provided email already exists."
            ) from exc
        elif "phone_number" in str(exc):
            raise ConflictError(
                "User creation failed. User with provided phone number already exists."
            ) from exc
        raise ConflictError from exc

    def create_user(
        self, email: str, password: str | None = None, **extra: Any
    ) -> User:
        user = self._prepare_user(email, password, **extra)
        try:
            user.save(using=self._db)
        except IntegrityError as exc:
            self._handle_integrity_error(exc)
        except Exception as exc:
            logger.error(
                "Unhandled error during sync user creation",
                email=email,
                error=str(exc),
            )
            raise BaseAPIException(
                "User creation failed. Please try again later."
            ) from exc
        return user

    async def acreate_user(
        self, email: str, password: str | None = None, **extra: Any
    ) -> User:
        user = self._prepare_user(email, password, **extra)
        try:
            await user.asave(using=self._db)
        except IntegrityError as exc:
            self._handle_integrity_error(exc)
        except Exception as exc:
            logger.error(
                "Unhandled error during async user creation",
                email=email,
                error=str(exc),
            )
            raise BaseAPIException(
                "User creation failed. Please try again later."
            ) from exc
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra: Any
    ) -> User:
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("user_type", "ADMIN")
        extra.setdefault("is_email_verified", True)

        return self.create_user(email, password, **extra)

    def get_by_natural_key(self, username: str) -> User:
        return self.get(email__iexact=username)
