import pickle  # noqa
import secrets
from datetime import UTC, datetime
from typing import Any, Dict, List
from uuid import UUID

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from core.application.event_bus import EventBus
from core.application.ports import (
    CacheServiceAdapterInterface,
    EmailServiceAdapterInterface,
    EventPublisherInterface,
    VerificationServiceAdapterInterface,
)
from core.domain.events import DomainEvent
from core.infrastructure.exceptions import BadRequestError, BaseAPIException
from core.infrastructure.logging.base import logger


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


class DjangoVerificationServiceAdapter(VerificationServiceAdapterInterface):
    def generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def generate_email_verification_link(
        self,
        verification_uuid: UUID,
        verification_token: str,
        is_business: bool = False,
    ) -> str:
        if is_business:
            path = reverse(
                "business_verification:verify-business-email",
                kwargs={
                    "verification_uuid": verification_uuid,
                    "verification_token": verification_token,
                },
            )
        else:
            path = reverse(
                "authentication:verify-email",
                kwargs={
                    "user_uuid": verification_uuid,
                    "verification_token": verification_token,
                },
            )

        verification_url = f"{settings.FROM_DOMAIN}{path}"
        return verification_url


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

    def send_business_verification_success_email(
        self,
        recipient_email: str,
        business_name: str,
        registration_number: str,
        provider_reference: str = None,
    ) -> None:
        context = {
            "business_name": business_name,
            "registration_number": registration_number,
            "verification_date": datetime.now(tz=UTC).strftime("%B %d, %Y"),
            "provider_reference": provider_reference,
        }
        try:
            self._send_template_email(
                subject=f"Business Verification Successful - {business_name}",
                template_name="business_verification_success",
                context=context,
                recipient_list=[recipient_email],
            )
        except Exception as e:
            logger.critical(
                f"Failed to send business verification success email for '{business_name}' to '{recipient_email}': {e}"
            )

    def send_business_verification_failed_email(
        self,
        recipient_email: str,
        business_name: str,
        registration_number: str,
        error_reason: str = None,
    ) -> None:
        context = {
            "business_name": business_name,
            "registration_number": registration_number,
            "verification_date": datetime.now(tz=UTC).strftime("%B %d, %Y"),
            "error_reason": error_reason
            or "Unable to verify business information with the provided details.",
        }
        try:
            self._send_template_email(
                subject=f"Business Verification Failed - {business_name}",
                template_name="business_verification_failure",
                context=context,
                recipient_list=[recipient_email],
            )
        except Exception as e:
            logger.critical(
                f"Failed to send business verification failed email for '{business_name}' to '{recipient_email}': {e}"
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


@shared_task
def _publish_event_to_bus(event_data: bytes) -> None:
    event = pickle.loads(event_data)
    EventBus.publish(event)


class DjangoEventPublisherAdapter(EventPublisherInterface):
    def publish(self, event: DomainEvent) -> None:
        event_data = pickle.dumps(event)
        _publish_event_to_bus.delay(event_data)
