from apps.authentication.application.rules import (
    LoginUserRule,
    LogoutUserRule,
    RegisterUserRule,
    RequestEmailVerificationRule,
    SocialAuthenticationRule,
    UpdateUserTypeRule,
    VerifyEmailRule,
)
from apps.authentication.domain.events import (
    UserEmailVerifiedEvent,
    UserLogoutEvent,
    UserUpdateEvent,
    UserVerificationEmailEvent,
)
from apps.authentication.infrastructure.event_handlers import (
    blacklist_jwt_token,
    cache_email_verification_status,
    send_verification_email_event,
    update_user_details,
    update_user_verification_status,
)
from apps.authentication.infrastructure.repositories import (
    DjangoBlackListedTokenRepository,
)
from apps.authentication.infrastructure.services import (
    DjangoJWTTokenAdapter,
    DjangoPasswordServiceAdapter,
    SocialAuthenticationAdapter,
)
from apps.users.infrastructure.repositories import DjangoUserRepository
from core.application.event_bus import EventBus
from core.infrastructure.factory import (
    get_cache_service,
    get_email_service,
    get_verification_service,
)
from core.infrastructure.services import DjangoEventPublisherAdapter


def get_user_repository():
    return DjangoUserRepository()


def get_password_service():
    return DjangoPasswordServiceAdapter()


def get_jwt_token_service():
    return DjangoJWTTokenAdapter()


def get_blacklisted_token_repository():
    return DjangoBlackListedTokenRepository()


def get_social_authentication_service():
    return SocialAuthenticationAdapter()


def get_event_publisher():
    return DjangoEventPublisherAdapter()


def get_register_user_rule():
    return RegisterUserRule(
        user_repository=get_user_repository(),
        password_service=get_password_service(),
        event_publisher=get_event_publisher(),
    )


def get_update_user_type_rule():
    return UpdateUserTypeRule(
        user_repository=get_user_repository(), event_publisher=get_event_publisher()
    )


def get_request_email_verification_rule():
    return RequestEmailVerificationRule(
        cache_service=get_cache_service(),
        event_publisher=get_event_publisher(),
        user_repository=get_user_repository(),
    )


def get_login_user_rule():
    return LoginUserRule(
        user_repository=get_user_repository(),
        password_service=get_password_service(),
        event_publisher=get_event_publisher(),
    )


def get_logout_user_rule():
    return LogoutUserRule(
        jwt_token_service=get_jwt_token_service(),
        event_publisher=get_event_publisher(),
    )


def get_verify_email_rule():
    return VerifyEmailRule(
        user_repository=get_user_repository(),
        cache_service=get_cache_service(),
        event_publisher=get_event_publisher(),
    )


def get_social_authentication_rule():
    return SocialAuthenticationRule(
        user_repository=get_user_repository(),
        social_authentication_service=get_social_authentication_service(),
        event_publisher=get_event_publisher(),
    )


def register_authentication_event_handlers():
    user_repository = get_user_repository()
    blacklisted_token_repository = get_blacklisted_token_repository()
    verification_service = get_verification_service()
    cache_service = get_cache_service()
    email_service = get_email_service()

    EventBus.subscribe(
        UserVerificationEmailEvent,
        lambda event: send_verification_email_event(
            event,
            user_repository,
            verification_service,
            cache_service,
            email_service,
        ),
    )
    EventBus.subscribe(
        UserEmailVerifiedEvent,
        lambda event: cache_email_verification_status(
            event, user_repository, cache_service
        ),
    )
    EventBus.subscribe(
        UserEmailVerifiedEvent,
        lambda event: update_user_verification_status(event, user_repository),
    )
    EventBus.subscribe(
        UserUpdateEvent, lambda event: update_user_details(event, user_repository)
    )
    EventBus.subscribe(
        UserLogoutEvent,
        lambda event: blacklist_jwt_token(event, blacklisted_token_repository),
    )
