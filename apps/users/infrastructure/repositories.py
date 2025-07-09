from typing import Any, Dict

from apps.users.application.ports import UserRepositoryInterface
from apps.users.domain.models import User as DomainUser
from apps.users.infrastructure.models import User
from core.infrastructure.exceptions import BaseAPIException
from core.infrastructure.logging.base import logger


class DjangoUserRepository(UserRepositoryInterface):
    def create(self, user: DomainUser) -> DomainUser:
        django_user = User.objects.create_user(**self._to_django_user_data(user))

        return self._to_domain_user_data(django_user)

    def create_social(self, user: DomainUser) -> User:
        return User.objects.create_user(**self._to_django_user_data(user))

    def update(
        self, user: DomainUser, return_raw: bool = True, **kwargs
    ) -> DomainUser | User:
        if not isinstance(user, DomainUser):
            user = self._to_domain_user_data(user)

        django_user = User.objects.get(id=user.id)
        django_user.email = user.email
        django_user.first_name = user.first_name
        django_user.last_name = user.last_name
        django_user.user_type = user.user_type
        django_user.is_email_verified = user.is_email_verified
        django_user.is_active = user.is_active
        django_user.is_staff = user.is_staff
        django_user.is_superuser = user.is_superuser
        django_user.uuid = user.uuid

        for key, value in kwargs.items():
            if hasattr(django_user, key):
                setattr(django_user, key, value)
        try:
            django_user.save()
        except Exception as e:
            logger.critical(
                f"Unhandled error during user update for '{user.email}': {e}"
            )
            raise BaseAPIException("User update failed. Please try again later.") from e

        if not return_raw:
            return self._to_domain_user_data(django_user)
        else:
            return django_user

    def get_by_id(self, user_id: int) -> DomainUser | None:
        try:
            django_user = User.objects.get(id=user_id)
            return self._to_domain_user_data(django_user)
        except User.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> DomainUser | None:
        try:
            django_user = User.objects.get(email=email)
            return self._to_domain_user_data(django_user)
        except User.DoesNotExist:
            return None

    def _to_django_user_data(self, domain_user: DomainUser) -> Dict[str, Any]:
        return {
            "email": domain_user.email,
            "password": domain_user.password_hash,
            "first_name": domain_user.first_name,
            "last_name": domain_user.last_name,
            "user_type": domain_user.user_type,
            "is_email_verified": domain_user.is_email_verified,
            "is_active": domain_user.is_active,
            "is_staff": domain_user.is_staff,
            "is_superuser": domain_user.is_superuser,
        }

    def _to_domain_user_data(self, django_user: User) -> DomainUser:
        return DomainUser(
            email=django_user.email,
            password_hash=django_user.password,
            first_name=django_user.first_name,
            last_name=django_user.last_name,
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
