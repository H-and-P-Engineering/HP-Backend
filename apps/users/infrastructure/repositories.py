from typing import Any, Dict

from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from social_core.utils import (
    partial_pipeline_data,
    user_is_active,
    user_is_authenticated,
)

from apps.users.application.ports import UserRepositoryInterface
from apps.users.domain.enums import UserType
from apps.users.domain.models import User as DomainUser
from apps.users.infrastructure.models import User
from core.infrastructure.exceptions import BadRequestError, BaseAPIException
from core.infrastructure.logging.base import logger


class DjangoUserRepository(UserRepositoryInterface):
    def create(self, user):
        django_user = User.objects.create_user(**self._to_django_user_data(user))
        return self._to_domain_user_data(django_user)

    def update(self, user, **kwargs):
        try:
            django_user = User.objects.get(id=user.id)

            django_user.email = user.email
            django_user.first_name = user.first_name
            django_user.last_name = user.last_name
            django_user.user_type = user.user_type
            django_user.is_email_verified = user.is_email_verified
            django_user.is_active = user.is_active

            for key, value in kwargs.items():
                if hasattr(django_user, key):
                    setattr(django_user, key, value)

            django_user.save()
            return self._to_domain_user_data(django_user)
        except Exception as e:
            logger.exception(
                f"Unknown error during user update for '{user.email}': {e}"
            )
            raise BaseAPIException(_("User update failed. Try again later.")) from e

    def get_by_id(self, user_id) -> DomainUser | None:
        try:
            django_user = User.objects.get(id=user_id)
            return self._to_domain_user_data(django_user)
        except User.DoesNotExist:
            return None

    def get_by_email(self, email) -> DomainUser | None:
        try:
            django_user = User.objects.get(email=email)
            return self._to_domain_user_data(django_user)
        except User.DoesNotExist:
            return None

    def get_or_create_social(self, request: Request):
        backend = request.backend
        user = request.user
        user_type = request.session.get("user_type", UserType.CLIENT)

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
            raise BadRequestError(
                _("Social authentication failed. Requested user account is inactive")
            )

        if not user_is_active(social_user):
            raise BadRequestError(
                _("Social authentication failed. This account has been deactivated")
            )

        user_model = backend.strategy.storage.user.user_model()
        if social_user and not isinstance(social_user, user_model):
            raise BadRequestError(
                _("Social authentication failed. User object is invalid.")
            )

        is_new_user = getattr(social_user, "is_new")

        domain_user = self._to_domain_user_data(social_user)
        domain_user.is_new = is_new_user

        return domain_user

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
            "uuid": domain_user.uuid,
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
