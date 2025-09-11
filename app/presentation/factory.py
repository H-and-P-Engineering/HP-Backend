from app.application.authentication.rules import (
    LoginUserRule,
    LogoutUserRule,
    RegisterUserRule,
    RequestEmailVerificationRule,
    SocialAuthenticationRule,
    VerifyEmailRule,
)
from app.application.business_verification.rules import (
    CreateBusinessProfileRule,
    InitiateBusinessVerificationRule,
    ProcessBusinessVerificationRule,
    RequestBusinessEmailVerificationRule,
    VerifyBusinessEmailRule,
)
from app.application.location.rules import ProcessLocationQueryRule
from app.application.users.rules import UpdateUserDataRule, UpdateUserTypeRule
from app.core.events import EventBus
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
from app.infrastructure.business_verification_service import BusinessVerificationService
from app.infrastructure.cache_service import DjangoCacheService
from app.infrastructure.email_service import (
    DjangoEmailService,
    DjangoVerificationService,
)
from app.infrastructure.event_handlers import (
    blacklist_jwt_token,
    cache_business_email_verification_status,
    cache_email_verification_status,
    cache_processed_location,
    process_business_verification_event,
    send_business_verification_email_event,
    send_business_verification_failed_email,
    send_business_verification_success_email,
    send_verification_email_event,
    update_business_email_verification_status,
    update_user_details,
    update_user_verification_status,
)
from app.infrastructure.event_publisher import EventPublisher
from app.infrastructure.jwt_service import check_access_token_expiry, create_jwt_tokens
from app.infrastructure.location.events import ProcessLocationEvent
from app.infrastructure.location_service import (
    GoogleGeocodingService,
    GooglePlacesService,
)
from app.infrastructure.password_service import hash_password, password_check
from app.infrastructure.social_auth_service import begin_social_auth
from app.infrastructure.users.events import UserUpdateEvent
from app.infrastructure.users.repositories import DjangoUserRepository


def get_user_repository():
    return DjangoUserRepository()


def get_business_verification_repository():
    return DjangoBusinessVerificationRepository()


def get_business_profile_repository():
    return DjangoBusinessProfileRepository()


def get_verification_service():
    return DjangoVerificationService()


def get_business_verification_service():
    return BusinessVerificationService()


def get_email_service():
    return DjangoEmailService()


def get_blacklisted_token_repository():
    return DjangoBlackListedTokenRepository()


def get_event_publisher():
    return EventPublisher()


def get_cache_service():
    return DjangoCacheService()


def get_register_user_rule():
    return RegisterUserRule(
        user_repository=get_user_repository(),
        hash_password=hash_password,
        event_publisher=get_event_publisher(),
    )


def get_update_data_rule():
    return UpdateUserDataRule(
        user_repository=get_user_repository(),
        hash_password=hash_password,
        event_publisher=get_event_publisher(),
    )


def get_update_user_type_rule():
    return UpdateUserTypeRule(
        user_repository=get_user_repository(), event_publisher=get_event_publisher()
    )


def get_request_email_verification_rule():
    return RequestEmailVerificationRule(
        user_repository=get_user_repository(),
        cache_service=get_cache_service(),
        event_publisher=get_event_publisher(),
    )


def get_login_user_rule():
    return LoginUserRule(
        user_repository=get_user_repository(),
        check_password=password_check,
        create_jwt_tokens=create_jwt_tokens,
        event_publisher=get_event_publisher(),
    )


def get_logout_user_rule():
    return LogoutUserRule(
        check_access_token_expiry=check_access_token_expiry,
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
        begin_social_auth=begin_social_auth,
        create_jwt_tokens=create_jwt_tokens,
        event_publisher=get_event_publisher(),
    )


def get_create_business_profile_rule():
    return CreateBusinessProfileRule(
        user_repository=get_user_repository(),
        business_profile_repository=get_business_profile_repository(),
    )


def get_verify_business_rule():
    return InitiateBusinessVerificationRule(
        business_verification_repository=get_business_verification_repository(),
        business_profile_repository=get_business_profile_repository(),
        user_repository=get_user_repository(),
        event_publisher=get_event_publisher(),
    )


def get_process_business_verification_rule():
    return ProcessBusinessVerificationRule(
        business_verification_repository=get_business_verification_repository(),
        business_profile_repository=get_business_profile_repository(),
        verification_service=get_business_verification_service(),
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


def get_process_location_query_rule():
    return ProcessLocationQueryRule(
        cache_service=get_cache_service(),
        geocoding_service=GoogleGeocodingService(),
        places_service=GooglePlacesService(),
        event_publisher=get_event_publisher(),
    )


def register_user_event_handlers():
    user_repository = get_user_repository()

    EventBus.subscribe(
        UserUpdateEvent,
        lambda event: update_user_details(event, user_repository),
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
        UserLogoutEvent,
        lambda event: blacklist_jwt_token(event, blacklisted_token_repository),
    )


def register_business_verification_event_handlers():
    process_business_verification_rule = get_process_business_verification_rule()
    business_verification_repository = get_business_verification_repository()
    business_profile_repository = get_business_profile_repository()
    email_service = get_email_service()
    verification_service = get_verification_service()
    cache_service = get_cache_service()

    EventBus.subscribe(
        BusinessVerificationRequestedEvent,
        lambda event: process_business_verification_event(
            event, process_business_verification_rule, BusinessVerificationStatusEvent
        ),
    )

    EventBus.subscribe(
        BusinessVerificationStatusEvent,
        lambda event: send_business_verification_success_email(
            event,
            email_service,
            cache_service,
            verification_service,
            business_verification_repository,
            business_profile_repository,
        ),
    )

    EventBus.subscribe(
        BusinessVerificationStatusEvent,
        lambda event: send_business_verification_failed_email(
            event, email_service, business_verification_repository
        ),
    )

    EventBus.subscribe(
        BusinessEmailVerificationRequestedEvent,
        lambda event: send_business_verification_email_event(
            event,
            business_verification_repository,
            verification_service,
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


def register_location_event_handlers():
    cache_service = get_cache_service()

    EventBus.subscribe(
        ProcessLocationEvent,
        lambda event: cache_processed_location(event, cache_service),
    )
