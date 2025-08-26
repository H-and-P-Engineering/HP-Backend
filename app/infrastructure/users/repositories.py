from typing import Any, Dict, Type

from loguru import logger
from social_core.utils import (
    partial_pipeline_data,
    user_is_active,
    user_is_authenticated,
)

from app.application.users.ports import IUserRepository
from app.core.exceptions import BaseAPIException
from app.domain.users.entities import User as DomainUser
from app.domain.users.enums import UserType

from .models.tables import User


def from_domain_user(domain_user: DomainUser) -> Dict[str, Any]:
    return {
        "email": domain_user.email,
        "password": domain_user.password_hash,
        "first_name": domain_user.first_name,
        "last_name": domain_user.last_name,
        "phone_number": domain_user.phone_number,
        "user_type": domain_user.user_type,
        "is_email_verified": domain_user.is_email_verified,
        "is_active": domain_user.is_active,
        "is_staff": domain_user.is_staff,
        "is_superuser": domain_user.is_superuser,
    }


def to_domain_user(django_user: User) -> DomainUser:
    return DomainUser(
        email=django_user.email,
        password_hash=django_user.password,
        first_name=django_user.first_name,
        last_name=django_user.last_name,
        phone_number=django_user.phone_number,
        user_type=django_user.user_type,
        is_email_verified=django_user.is_email_verified,
        is_active=django_user.is_active,
        is_staff=django_user.is_staff,
        is_superuser=django_user.is_superuser,
        id=django_user.id,
        uuid=django_user.uuid,
        created_at=django_user.created_at,
        updated_at=django_user.updated_at,
        last_login=django_user.last_login,
    )


class DjangoUserRepository(IUserRepository):
    def create(self, user: DomainUser) -> DomainUser:
        django_user = User.objects.create_user(**from_domain_user(user))

        domain_user = to_domain_user(django_user)
        domain_user.is_new = True
        return domain_user

    def update(self, user: DomainUser, **kwargs) -> DomainUser:
        try:
            django_user = User.objects.get(id=user.id)

            for key, value in kwargs.items():
                if (
                    hasattr(django_user, key)
                    and key not in ["password", "password_hash", "created_at"]
                    and value not in [UserType.ADMIN]
                ):
                    setattr(django_user, key, value)

            django_user.save()
            return to_domain_user(django_user)
        except Exception as e:
            logger.error(f"Unhandled error during user update for '{user.email}': {e}")
            raise BaseAPIException("User update failed. Please try again later.") from e

    def get_by_id(self, user_id: int) -> DomainUser | None:
        try:
            django_user = User.objects.get(id=user_id)
            return to_domain_user(django_user)
        except User.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> DomainUser | None:
        try:
            django_user = User.objects.get(email=email)
            return to_domain_user(django_user)
        except User.DoesNotExist:
            return None

    def create_social_user(self, user: DomainUser) -> User:
        return User.objects.create_user(**from_domain_user(user))

    def get_or_create_social_user(self, request: Any) -> DomainUser:
        backend = request.backend
        user = request.user
        user_type = request.session.get("user_type", UserType.BUYER)

        if "user_type" in request.session:
            del request.session["user_type"]

        is_user_authenticated = user_is_authenticated(user)

        user = user if is_user_authenticated else None

        partial = partial_pipeline_data(backend, user)
        if partial:
            social_user = backend.continue_pipeline(partial, user_type=user_type)
            backend.clean_partial_pipeline(partial.token)
        else:
            social_user = backend.complete(user=user, user_type=user_type)

        if not social_user:
            raise BaseAPIException(
                "Social authentication failed. Requested user account is inactive"
            )

        if not user_is_active(social_user):
            raise BaseAPIException(
                "Social authentication failed. This account has been deactivated"
            )

        user_model = backend.strategy.storage.user.user_model()
        if social_user and not isinstance(social_user, user_model):
            raise BaseAPIException(
                "Social authentication failed. User object is invalid."
            )

        is_new_user = getattr(social_user, "is_new")

        domain_user = to_domain_user(social_user)
        domain_user.is_new = is_new_user

        return domain_user
