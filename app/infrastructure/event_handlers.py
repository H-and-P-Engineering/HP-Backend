from typing import Any, Callable

from app.infrastructure.authentication.events import (
    UserEmailVerifiedEvent,
    UserLogoutEvent,
    UserVerificationEmailEvent,
)
from app.infrastructure.authentication.repositories import (
    DjangoBlackListedTokenRepository,
)
from app.infrastructure.business_verification.events import (
    BusinessEmailVerificationRequestedEvent,
    BusinessEmailVerificationSuccessfulEvent,
    BusinessVerificationRequestedEvent,
    BusinessVerificationStatusEvent,
)
from app.infrastructure.business_verification.repositories import (
    DjangoBusinessProfileRepository,
    DjangoBusinessVerificationRepository,
)
from app.infrastructure.cache_service import DjangoCacheService
from app.infrastructure.email_service import (
    DjangoEmailService,
    DjangoVerificationService,
)
from app.infrastructure.users.events import UserUpdateEvent
from app.infrastructure.users.repositories import DjangoUserRepository


def send_verification_email_event(
    event: UserVerificationEmailEvent,
    user_repository: DjangoUserRepository,
    verification_service: DjangoVerificationService,
    cache_service: DjangoCacheService,
    email_service: DjangoEmailService,
) -> None:
    user = user_repository.get_by_id(event.user_id)
    if user:
        token = verification_service.generate_token()
        cache_service.set(f"email_verify_{str(user.uuid)}", (user.id, token))
        link = verification_service.generate_email_verification_link(user.uuid, token)
        email_service.send_verification_email(user.email, verification_link=link)


def cache_email_verification_status(
    event: UserEmailVerifiedEvent,
    user_repository: DjangoUserRepository,
    cache_service: DjangoCacheService,
) -> None:
    user = user_repository.get_by_id(event.user_id)
    if user:
        cache_service.delete(f"email_verify_{user.uuid}")
        cache_service.set(f"{user.email}_verified", str(user.email))


def update_user_verification_status(
    event: UserEmailVerifiedEvent, user_repository: DjangoUserRepository
) -> None:
    user = user_repository.get_by_id(event.user_id)
    if user:
        user_repository.update(user, is_email_verified=True)


def update_user_details(
    event: UserUpdateEvent, user_repository: DjangoUserRepository
) -> None:
    update_fields, user_id = event.update_fields, event.user_id

    user = user_repository.get_by_id(user_id)
    if user:
        user_repository.update(user, **update_fields)


def blacklist_jwt_token(
    event: UserLogoutEvent,
    blacklisted_token_repository: DjangoBlackListedTokenRepository,
) -> None:
    token, _user_id = event.token, event.user_id
    if token:
        blacklisted_token_repository.create(token)


def process_business_verification_event(
    event: BusinessVerificationRequestedEvent,
    process_business_verification: Callable[[Any, Any], Any],
    sub_event: Callable[[Any], Any],
) -> None:
    process_business_verification(event.verification_id, sub_event)


def send_business_verification_success_email(
    event: BusinessVerificationStatusEvent,
    email_service: DjangoEmailService,
    cache_service: DjangoCacheService,
    verification_service: DjangoVerificationService,
    business_verification_repository: DjangoBusinessVerificationRepository,
    business_profile_repository: DjangoBusinessProfileRepository,
) -> None:
    if event.success:
        verification = business_verification_repository.get_by_id(event.verification_id)
        profile = business_profile_repository.get_by_verification_id(
            event.verification_id
        )

        if not verification or not profile:
            return

        email_service.send_business_verification_success_email(
            recipient_email=verification.business_email,
            business_name=verification.business_name,
            registration_number=verification.business_registration_number,
            provider_reference=verification.verification_provider_reference,
        )

        if not profile.is_business_email_verified:
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


def send_business_verification_failed_email(
    event: BusinessVerificationStatusEvent,
    email_service: DjangoEmailService,
    business_verification_repository: DjangoBusinessVerificationRepository,
) -> None:
    if not event.success:
        verification = business_verification_repository.get_by_id(event.verification_id)
        if not verification:
            return

        email_service.send_business_verification_failed_email(
            recipient_email=event.business_email,
            business_name=event.business_name,
            registration_number=verification.business_registration_number,
            error_reason=event.error_reason,
        )


def send_business_verification_email_event(
    event: BusinessEmailVerificationRequestedEvent,
    business_verification_repository: DjangoBusinessVerificationRepository,
    verification_service: DjangoVerificationService,
    cache_service: DjangoCacheService,
    email_service: DjangoEmailService,
) -> None:
    verification = business_verification_repository.get_by_id(event.verification_id)
    if verification:
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
    cache_service: DjangoCacheService,
) -> None:
    verification = business_verification_repository.get_by_id(event.verification_id)
    if verification:
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
    if business_profile:
        business_profile_repository.update(
            business_profile, is_business_email_verified=True
        )
