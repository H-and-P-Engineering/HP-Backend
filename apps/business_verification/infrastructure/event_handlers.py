from typing import Any

from apps.business_verification.domain.events import (
    BusinessEmailVerificationSuccessfulEvent,
    BusinessVerificationEmailEvent,
    BusinessVerificationFailedEvent,
    BusinessVerificationRequestedEvent,
    BusinessVerificationSuccessfulEvent,
)
from apps.business_verification.infrastructure.repositories import (
    DjangoBusinessProfileRepository,
    DjangoBusinessVerificationRepository,
)
from core.infrastructure.logging.base import logger
from core.infrastructure.services import (
    DjangoCacheServiceAdapter,
    DjangoEmailServiceAdapter,
    DjangoVerificationServiceAdapter,
)


def process_business_verification_event(
    event: BusinessVerificationRequestedEvent, process_business_verification_rule: Any
) -> None:
    process_business_verification_rule.execute(event.verification_id)


def send_business_verification_success_email(
    event: BusinessVerificationSuccessfulEvent,
    email_service: DjangoEmailServiceAdapter,
    business_verification_repository: DjangoBusinessVerificationRepository,
) -> None:
    try:
        verification = business_verification_repository.get_by_id(event.verification_id)
        if not verification:
            logger.error(f"Verification not found for ID: {event.verification_id}")
            return

        email_service.send_business_verification_success_email(
            recipient_email=verification.business_email,
            business_name=verification.business_name,
            registration_number=verification.business_registration_number,
            provider_reference=verification.verification_provider_reference,
        )
        logger.info(
            f"Business verification success email sent for verification ID: {event.verification_id}"
        )
    except Exception as e:
        logger.error(f"Failed to send business verification success email: {e}")


def send_business_verification_failed_email(
    event: BusinessVerificationFailedEvent,
    email_service: DjangoEmailServiceAdapter,
    business_verification_repository: DjangoBusinessVerificationRepository,
) -> None:
    try:
        verification = business_verification_repository.get_by_id(event.verification_id)
        if not verification:
            logger.error(f"Verification not found for ID: {event.verification_id}")
            return

        email_service.send_business_verification_failed_email(
            recipient_email=event.business_email,
            business_name=event.business_name,
            registration_number=verification.business_registration_number,
            error_reason=event.error_reason,
        )
        logger.info(
            f"Business verification failure email sent for verification ID: {event.verification_id}"
        )
    except Exception as e:
        logger.error(f"Failed to send business verification failed email: {e}")


def send_business_verification_email_event(
    event: BusinessVerificationEmailEvent,
    business_verification_repository: DjangoBusinessVerificationRepository,
    verification_service: DjangoVerificationServiceAdapter,
    cache_service: DjangoCacheServiceAdapter,
    email_service: DjangoEmailServiceAdapter,
) -> None:
    verification = business_verification_repository.get_by_id(event.verification_id)

    token = verification_service.generate_token()

    cache_service.set(
        f"email_verify_{str(verification.uuid)}", (verification.id, token)
    )

    link = verification_service.generate_email_verification_link(
        verification.uuid, token, is_business=True
    )

    email_service.send_verification_email(
        verification.business_email, verification_link=link
    )


def cache_business_email_verification_status(
    event: BusinessEmailVerificationSuccessfulEvent,
    business_verification_repository: DjangoBusinessVerificationRepository,
    cache_service: DjangoCacheServiceAdapter,
) -> None:
    verification = business_verification_repository.get_by_id(event.verification_id)

    cache_service.delete(f"email_verify_{verification.uuid}")
    cache_service.set(
        f"{verification.business_email}_verified", str(verification.business_email)
    )


def update_business_email_verification_status(
    event: BusinessEmailVerificationSuccessfulEvent,
    business_profile_repository: DjangoBusinessProfileRepository,
) -> None:
    business_profile = business_profile_repository.get_by_verification_id(
        event.verification_id
    )

    business_profile_repository.update(
        business_profile, is_business_email_verified=True
    )
