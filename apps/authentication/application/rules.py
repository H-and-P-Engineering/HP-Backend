from datetime import UTC, datetime
from typing import Any

from apps.authentication.application.ports import (
    JWTTokenAdapterInterface,
    PasswordServiceAdapterInterface,
    SocialAuthenticationAdapterInterface,
)
from apps.authentication.domain.events import (
    UserEmailVerifiedEvent,
    UserLogoutEvent,
    UserUpdateEvent,
    UserVerificationEmailEvent,
)
from apps.authentication.domain.models import BlackListedToken
from apps.users.application.ports import UserRepositoryInterface
from apps.users.domain.models import User as DomainUser
from apps.users.domain.models import UserType as DomainUserType
from core.application.exceptions import BusinessRuleException
from core.application.ports import CacheServiceAdapterInterface, EventPublisherInterface


class RegisterUserRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordServiceAdapterInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service
        self._event_publisher = event_publisher

    def execute(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        user_type: str,
    ) -> DomainUser:
        password_hash = self._password_service.hash(password)

        user = DomainUser(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            user_type=DomainUserType(
                user_type.upper() if isinstance(user_type, str) else user_type
            ),
            is_new=True,
        )

        created_user = self._user_repository.create(user)

        self._event_publisher.publish(UserVerificationEmailEvent(created_user.id))

        return created_user


class UpdateUserTypeRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._user_repository = user_repository
        self._event_publisher = event_publisher

    def execute(self, email: str, user_type: str) -> None:
        user = self._user_repository.get_by_email(email)
        if not user:
            raise BusinessRuleException(
                "User type update failed. Provided email is invalid."
            )

        self._event_publisher.publish(
            UserUpdateEvent(update_fields={"user_type": user_type}, user_id=user.id)
        )


class RequestEmailVerificationRule:
    def __init__(
        self,
        cache_service: CacheServiceAdapterInterface,
        event_publisher: EventPublisherInterface,
        user_repository: UserRepositoryInterface | None = None,
    ) -> None:
        self._cache_service = cache_service
        self._user_repository = user_repository
        self._event_publisher = event_publisher

    def execute(self, email: str, user: DomainUser | None = None) -> None:
        if self._cache_service.get(f"{email}_verified"):
            raise BusinessRuleException(
                "Email verification request failed. User email is already verified."
            )

        user = user or self._user_repository.get_by_email(email)

        if not user:
            raise BusinessRuleException(
                "Email verification request failed. Provided email is invalid."
            )

        if user.is_email_verified:
            self._event_publisher.publish(UserEmailVerifiedEvent(user.id))
            raise BusinessRuleException(
                "Email verification request failed. User email is already verified."
            )

        self._event_publisher.publish(UserVerificationEmailEvent(user.id))


class VerifyEmailRule:
    def __init__(
        self,
        cache_service: CacheServiceAdapterInterface,
        user_repository: UserRepositoryInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._cache_service = cache_service
        self._user_repository = user_repository
        self._event_publisher = event_publisher

    def execute(self, user_uuid: str, token: str) -> None:
        cached_data = self._cache_service.get(f"email_verify_{user_uuid}")
        if cached_data:
            cached_id, cached_token = cached_data
        else:
            raise BusinessRuleException(
                "Email verification failed. Verification session is invalid or expired."
            )

        user = self._user_repository.get_by_id(cached_id)

        if user and user.is_email_verified:
            raise BusinessRuleException(
                "Email verification failed. User email is already verified."
            )

        if not user or str(user.uuid) != str(user_uuid) or cached_token != token:
            raise BusinessRuleException(
                "Email verification failed. Provided user id or verification token is invalid."
            )

        self._event_publisher.publish(UserEmailVerifiedEvent(user.id))


class LoginUserRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordServiceAdapterInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service
        self._event_publisher = event_publisher

    def execute(self, email: str, password: str) -> DomainUser:
        user = self._user_repository.get_by_email(email)

        if not user or not self._password_service.check(password, user.password_hash):
            raise BusinessRuleException(
                "Login failed. Provided email or password is invalid."
            )

        if not user.is_active:
            raise BusinessRuleException(
                "Login failed. Requested user account is deactivated."
            )

        if not user.is_email_verified:
            raise BusinessRuleException(
                "Login failed. Requested user email is not verified. Please verify your email."
            )

        self._event_publisher.publish(
            UserUpdateEvent(
                update_fields={"last_login": datetime.now(tz=UTC)}, user_id=user.id
            )
        )

        return user


class LogoutUserRule:
    def __init__(
        self,
        jwt_token_service: JWTTokenAdapterInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._jwt_token_service = jwt_token_service
        self._event_publisher = event_publisher

    def execute(self, user_id: int, access_token: str) -> None:
        token_expiry = self._jwt_token_service.check_access_token_expiry(access_token)

        token = BlackListedToken(
            access=access_token, user_id=user_id, expires_at=token_expiry
        )

        self._event_publisher.publish(UserLogoutEvent(token=token, user_id=user_id))


class SocialAuthenticationRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        social_authentication_service: SocialAuthenticationAdapterInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._user_repository = user_repository
        self._social_authentication_service = social_authentication_service
        self._event_publisher = event_publisher

    def begin_authentication(self, request: Any, user_type: str) -> Any:
        return self._social_authentication_service.begin(request, user_type=user_type)

    def complete_authentication(self, request: Any) -> Any:
        user = self._user_repository.get_or_create_social(request)
        if user and not user.is_new:
            self._event_publisher.publish(
                UserUpdateEvent(
                    update_fields={"last_login": datetime.now(tz=UTC)}, user_id=user.id
                )
            )

        return user
