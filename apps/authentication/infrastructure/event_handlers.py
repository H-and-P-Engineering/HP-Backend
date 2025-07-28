from apps.authentication.domain.events import (
    UserEmailVerifiedEvent,
    UserLogoutEvent,
    UserUpdateEvent,
    UserVerificationEmailEvent,
)
from apps.authentication.infrastructure.repositories import (
    DjangoBlackListedTokenRepository,
)
from apps.authentication.infrastructure.services import (
    DjangoCacheServiceAdapter,
    DjangoEmailServiceAdapter,
    DjangoVerificationServiceAdapter,
)
from apps.users.infrastructure.repositories import DjangoUserRepository


def send_verification_email_event(
    event: UserVerificationEmailEvent,
    user_repository: DjangoUserRepository,
    verification_service: DjangoVerificationServiceAdapter,
    cache_service: DjangoCacheServiceAdapter,
    email_service: DjangoEmailServiceAdapter,
) -> None:
    user = user_repository.get_by_id(event.user_id)

    token = verification_service.generate_token()

    cache_service.set(f"email_verify_{str(user.uuid)}", (user.id, token))

    link = verification_service.generate_email_verification_link(user.uuid, token)

    email_service.send_verification_email(user.email, verification_link=link)


def cache_email_verification_status(
    event: UserEmailVerifiedEvent,
    user_repository: DjangoUserRepository,
    cache_service: DjangoCacheServiceAdapter,
) -> None:
    user = user_repository.get_by_id(event.user_id)

    cache_service.delete(f"email_verify_{user.uuid}")
    cache_service.set(f"{user.email}_verified", str(user.email))


def update_user_verification_status(
    event: UserEmailVerifiedEvent, user_repository: DjangoUserRepository
) -> None:
    user = user_repository.get_by_id(event.user_id)

    user_repository.update(user, is_email_verified=True)


def update_user_details(
    event: UserUpdateEvent, user_repository: DjangoUserRepository
) -> None:
    update_fields, user_id = event.update_fields, event.user_id

    user = user_repository.get_by_id(user_id)

    user_repository.update(user, **update_fields)


def blacklist_jwt_token(
    event: UserLogoutEvent,
    blacklisted_token_repository: DjangoBlackListedTokenRepository,
) -> None:
    token, _user_id = event.token, event.user_id

    blacklisted_token_repository.add(token)
