import json
import secrets
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from django.conf import settings
from django.core.cache import cache
from loguru import logger
from uuid6 import UUID

from core.enums import EmailType, EmailTypes
from core.exceptions import BadRequestError
from core.tasks import delete_cache_task, send_email_task, set_cache_task


class BaseCacheService:
    def __init__(self, prefix: str, timeout: int | None = None) -> None:
        self.prefix = prefix
        self.default_timeout = timeout

    def _get_key(self, key: str | UUID) -> str:
        return f"{self.prefix}:{str(key)}"

    def get(self, key: str | UUID) -> Any | None:
        cache_key = self._get_key(key)
        data = cache.get(cache_key)
        if data:
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data
        return None

    def set(self, key: str | UUID, value: Any, timeout: int | None = None) -> None:
        cache_key = self._get_key(key)
        serialized_value = json.dumps(value) if not isinstance(value, str) else value
        set_cache_task.delay(
            cache_key, serialized_value, timeout or self.default_timeout
        )

    def delete(self, key: str | UUID) -> None:
        cache_key = self._get_key(key)
        delete_cache_task.delay(cache_key)


class TokenCacheService(BaseCacheService):
    def __init__(self) -> None:
        super().__init__(
            prefix="verification_token",
            timeout=settings.DJANGO_VERIFICATION_TOKEN_EXPIRY * 60,
        )


class VerificationService:
    def __init__(self, cache: TokenCacheService | None = None) -> None:
        self.cache = cache or TokenCacheService()

    def generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def generate_verification_link(
        self,
        verification_uuid: UUID | str,
        verification_token: str,
    ) -> str:
        verification_url = f"{settings.FRONTEND_VERIFICATION_URL}/{verification_uuid}/{verification_token}/"
        return verification_url

    def store_token(self, user_uuid: UUID | str, token: str) -> None:
        self.cache.set(token, str(user_uuid))

    def run(self, verification_uuid: UUID | str) -> str:
        token = self.generate_token()
        self.store_token(verification_uuid, token)

        verification_link = self.generate_verification_link(verification_uuid, token)
        return verification_link

    def validate_token(self, user_uuid: UUID | str, token: str) -> bool:
        stored_uuid = self.cache.get(token)

        if not stored_uuid:
            logger.warning(
                "Token validation failed: not found or expired",
                token_prefix=token[:10],
            )
            raise BadRequestError(
                "Token validation failed: Token not found or expired."
            )

        if str(stored_uuid) != str(user_uuid):
            logger.warning(
                "Token validation failed: invalid token",
                user_uuid=str(user_uuid),
            )
            raise BadRequestError("Token validation failed: Invalid token.")

        self.cache.delete(token)
        return True


class EmailService:
    @staticmethod
    def send_template_email(
        subject: str,
        template_name: str,
        context: dict,
        recipient_list: Sequence[str],
        from_email: str | None = None,
    ) -> None:
        send_email_task.delay(
            subject=subject,
            template_name=template_name,
            context=context,
            recipient_list=recipient_list,
            from_email=from_email,
        )

    def send_standard_email(
        self,
        email_type: EmailType,
        context: dict,
        recipient_list: Sequence[str],
        subject_prefix: str = "",
        from_email: str | None = None,
    ) -> None:
        subject = f"{subject_prefix}{email_type.subject}"
        self.send_template_email(
            subject=subject,
            template_name=email_type.template_name,
            context=context,
            recipient_list=recipient_list,
            from_email=from_email,
        )

    def send_verification_email(
        self, recipient_email: str, verification_link: str
    ) -> None:
        context = {
            "email": recipient_email,
            "expiry_minutes": settings.DJANGO_VERIFICATION_TOKEN_EXPIRY,
            "verification_link": verification_link,
        }

        self.send_standard_email(
            email_type=EmailTypes.USER_VERIFICATION,
            context=context,
            recipient_list=[recipient_email],
        )

    def send_business_verification_email(
        self,
        recipient_email: str,
        verification_link: str,
        business_name: str | None = None,
        registration_number: str | None = None,
    ) -> None:
        context = {
            "email": recipient_email,
            "expiry_minutes": settings.DJANGO_VERIFICATION_TOKEN_EXPIRY,
            "verification_link": verification_link,
            "is_business": True,
            "business_name": business_name,
            "registration_number": registration_number,
        }

        self.send_standard_email(
            email_type=EmailTypes.BUSINESS_VERIFICATION,
            context=context,
            recipient_list=[recipient_email],
        )

    def send_business_verification_success_email(
        self,
        recipient_email: str,
        business_name: str,
        registration_number: str,
        provider_reference: str | None = None,
    ) -> None:
        context = {
            "business_name": business_name,
            "registration_number": registration_number,
            "verification_date": datetime.now(tz=UTC).strftime("%B %d, %Y"),
            "provider_reference": provider_reference,
        }

        self.send_standard_email(
            email_type=EmailTypes.BUSINESS_VERIFICATION_SUCCESS,
            context=context,
            recipient_list=[recipient_email],
            subject_prefix=f"{business_name} - ",
        )

    def send_business_verification_failed_email(
        self,
        recipient_email: str,
        business_name: str,
        registration_number: str,
        error_reason: str | None = None,
    ) -> None:
        context = {
            "business_name": business_name,
            "registration_number": registration_number,
            "verification_date": datetime.now(tz=UTC).strftime("%B %d, %Y"),
            "error_reason": error_reason
            or "Unable to verify business information with the provided details.",
        }

        self.send_standard_email(
            email_type=EmailTypes.BUSINESS_VERIFICATION_FAILURE,
            context=context,
            recipient_list=[recipient_email],
            subject_prefix=f"{business_name} - ",
        )
