import pickle  # noqa
import secrets
from datetime import UTC, datetime
from typing import Any, Dict, List
from uuid import UUID

from celery import shared_task
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from social_core.actions import do_auth
from social_core.utils import partial_pipeline_data

from apps.authentication.application.ports import (
    CacheServiceAdapterInterface,
    EmailServiceAdapterInterface,
    EventPublisherInterface,
    JWTTokenAdapterInterface,
    PasswordServiceAdapterInterface,
    SocialAuthenticationAdapterInterface,
    VerificationServiceAdapterInterface,
)
from apps.users.domain.enums import UserType
from apps.users.domain.models import User as DomainUser
from apps.users.infrastructure.repositories import DjangoUserRepository
from core.application.event_bus import EventBus
from core.domain.events import DomainEvent
from core.infrastructure.exceptions import BadRequestError, BaseAPIException
from core.infrastructure.logging.base import logger


class DjangoPasswordServiceAdapter(PasswordServiceAdapterInterface):
    def hash(self, password: str) -> str:
        return make_password(password)

    def check(self, raw_password: str, hashed_password: str) -> bool:
        return check_password(raw_password, hashed_password)


class DjangoVerificationServiceAdapter(VerificationServiceAdapterInterface):
    def generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def generate_email_verification_link(
        self, user_uuid: UUID, verification_token: str
    ) -> str:
        path = reverse(
            "authentication:verify-email",
            kwargs={
                "user_uuid": user_uuid,
                "verification_token": verification_token,
            },
        )
        verification_url = f"{settings.FROM_DOMAIN}{path}"
        return verification_url


class DjangoCacheServiceAdapter(CacheServiceAdapterInterface):
    def get(self, key: str) -> Any:
        return cache.get(key, None)

    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        timeout = timeout or settings.DJANGO_CACHE_TIMEOUT
        cache.set(key, value, timeout)

    def delete(self, key: str) -> None:
        try:
            cache.delete(key)
        except Exception:
            pass


class DjangoEmailServiceAdapter(EmailServiceAdapterInterface):
    def send_verification_email(
        self, recipient_email: str, verification_link: str
    ) -> None:
        context = {
            "email": recipient_email,
            "expiry_minutes": settings.DJANGO_VERIFICATION_TOKEN_EXPIRY,
            "verification_link": verification_link,
        }
        try:
            self._send_template_email(
                subject="Verify your email address",
                template_name="verify_email",
                context=context,
                recipient_list=[recipient_email],
            )
        except Exception as e:
            logger.critical(
                f"Unhandled error while sending verification email for '{recipient_email}': {e}"
            )
            raise BaseAPIException(
                "Failed to send verification email. Please try again later."
            )

    def _send_template_email(
        self,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        recipient_list: List[str],
        from_email: str | None = None,
    ) -> int:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        html_content = render_to_string(f"{template_name}.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list,
        )
        email.attach_alternative(html_content, "text/html")
        return email.send()


class DjangoJWTTokenAdapter(JWTTokenAdapterInterface):
    def create_tokens(self, user) -> dict:
        refresh = RefreshToken.for_user(user)
        tokens = {"refresh": str(refresh), "access": str(refresh.access_token)}
        return tokens

    def check_access_token_expiry(self, access_token: str) -> datetime:
        try:
            access = AccessToken(access_token)
            expires_at = datetime.fromtimestamp(access.get("exp"), tz=UTC)
        except (TokenError, ExpiredTokenError, InvalidToken) as e:
            raise ValidationError("Access token is invalid.") from e
        return expires_at


class SocialAuthenticationAdapter(SocialAuthenticationAdapterInterface):
    def begin(self, request: Any, user_type: str) -> Any:
        return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)

    def get_or_create_social(self, request: Any) -> Dict[str, DomainUser | bool]:
        backend = request.backend
        user = request.user

        is_user_authenticated = getattr(user, "is_authenticated", False)
        user = user if is_user_authenticated else None

        partial = partial_pipeline_data(backend, user)
        if partial:
            social_user = backend.continue_pipeline(partial)
            backend.clean_partial_pipeline(partial.token)
        else:
            social_user = backend.complete(user=user)

        if not social_user:
            raise BadRequestError(
                "Social authentication failed. Requested user account is inactive."
            )

        if not getattr(social_user, "is_active", False):
            raise BadRequestError(
                "Social authentication failed. This account has been deactivated."
            )

        user_model = backend.strategy.storage.user.user_model()
        if social_user and not isinstance(social_user, user_model):
            raise BadRequestError(
                "Social authentication failed. User object is invalid."
            )

        is_new_user = getattr(social_user, "is_new", False)

        return {"user": social_user, "is_new_user": is_new_user}


@shared_task
def _publish_event_to_bus(event_data: bytes) -> None:
    event = pickle.loads(event_data)
    EventBus.publish(event)


class DjangoEventPublisherAdapter(EventPublisherInterface):
    def publish(self, event: DomainEvent) -> None:
        event_data = pickle.dumps(event)
        _publish_event_to_bus.delay(event_data)
