from django.conf import settings

from apps.business_verification.application.rules import (
    CreateBusinessProfileRule,
    InitiateBusinessVerificationRule,
    ProcessBusinessVerificationRule,
    RequestBusinessEmailVerificationRule,
    VerifyBusinessEmailRule,
)
from apps.business_verification.domain.events import (
    BusinessEmailVerificationSuccessfulEvent,
    BusinessVerificationEmailEvent,
    BusinessVerificationFailedEvent,
    BusinessVerificationRequestedEvent,
    BusinessVerificationSuccessfulEvent,
)
from apps.business_verification.infrastructure.event_handlers import (
    cache_business_email_verification_status,
    process_business_verification_event,
    send_business_verification_email_event,
    send_business_verification_failed_email,
    send_business_verification_success_email,
    update_business_email_verification_status,
)
from apps.business_verification.infrastructure.repositories import (
    DjangoBusinessProfileRepository,
    DjangoBusinessVerificationRepository,
)
from apps.business_verification.infrastructure.services import YouVerifyAdapter
from apps.users.infrastructure.repositories import DjangoUserRepository
from core.application.event_bus import EventBus
from core.infrastructure.factory import get_cache_service, get_email_service
from core.infrastructure.factory import (
    get_verification_service as get_core_verification_service,
)
from core.infrastructure.services import DjangoEventPublisherAdapter


def get_business_verification_repository():
    return DjangoBusinessVerificationRepository()


def get_business_profile_repository():
    return DjangoBusinessProfileRepository()


def get_verification_service():
    if settings.BUSINESS_VERIFICATION_PROVIDER == "youverify":
        return YouVerifyAdapter()


def get_user_repository():
    return DjangoUserRepository()


def get_event_publisher():
    return DjangoEventPublisherAdapter()


def get_create_business_profile_rule():
    return CreateBusinessProfileRule(
        user_repository=get_user_repository(),
        business_profile_repository=get_business_profile_repository(),
    )


def get_verify_business_rule():
    return InitiateBusinessVerificationRule(
        business_verification_repository=get_business_verification_repository(),
        business_profile_repository=get_business_profile_repository(),
        verification_service=get_verification_service(),
        user_repository=get_user_repository(),
        event_publisher=get_event_publisher(),
    )


def get_process_business_verification_rule():
    return ProcessBusinessVerificationRule(
        business_verification_repository=get_business_verification_repository(),
        business_profile_repository=get_business_profile_repository(),
        verification_service=get_verification_service(),
        event_publisher=get_event_publisher(),
    )


def get_verify_business_email_rule():
    return VerifyBusinessEmailRule(
        cache_service=get_cache_service(),
        business_profile_repository=get_business_profile_repository(),
        business_verification_repository=get_business_verification_repository(),
        event_publisher=get_event_publisher(),
    )


def get_business_email_verification_request_rule():
    return RequestBusinessEmailVerificationRule(
        cache_service=get_cache_service(),
        business_verification_repository=get_business_verification_repository(),
        event_publisher=get_event_publisher(),
    )


def register_business_verification_event_handlers():
    process_business_verification_rule = get_process_business_verification_rule()
    business_verification_repository = get_business_verification_repository()
    business_profile_repository = get_business_profile_repository()
    email_service = get_email_service()
    auth_verification_service = get_core_verification_service()
    cache_service = get_cache_service()

    EventBus.subscribe(
        BusinessVerificationRequestedEvent,
        lambda event: process_business_verification_event(
            event, process_business_verification_rule
        ),
    )

    EventBus.subscribe(
        BusinessVerificationSuccessfulEvent,
        lambda event: send_business_verification_success_email(
            event, email_service, business_verification_repository
        ),
    )

    EventBus.subscribe(
        BusinessVerificationFailedEvent,
        lambda event: send_business_verification_failed_email(
            event, email_service, business_verification_repository
        ),
    )

    EventBus.subscribe(
        BusinessVerificationEmailEvent,
        lambda event: send_business_verification_email_event(
            event,
            business_verification_repository,
            auth_verification_service,
            cache_service,
            email_service,
        ),
    )

    EventBus.subscribe(
        BusinessEmailVerificationSuccessfulEvent,
        lambda event: cache_business_email_verification_status(
            event, business_verification_repository, cache_service
        ),
    )

    EventBus.subscribe(
        BusinessEmailVerificationSuccessfulEvent,
        lambda event: update_business_email_verification_status(
            event,
            business_profile_repository,
        ),
    )
