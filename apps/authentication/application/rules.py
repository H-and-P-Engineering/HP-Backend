from datetime import UTC, datetime
from typing import Any, Dict

from apps.authentication.domain.models import BlackListedToken, User, UserType
from apps.authentication.domain.ports import (
    BlackListedTokenRepositoryInterface,
    CacheServiceAdapterInterface,
    EmailServiceAdapterInterface,
    JWTTokenAdapterInterface,
    PasswordServiceAdapterInterface,
    SocialAuthenticationAdapterInterface,
    UserRepositoryInterface,
    VerificationServiceAdapterInterface,
)
from core.application.exceptions import BusinessRuleException


class RegisterUserRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordServiceAdapterInterface,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service

    def execute(
        self, email: str, password: str, first_name: str, last_name: str, user_type: str
    ) -> User:
        self._password_service.validate(password)
        password_hash = self._password_service.hash(password)

        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            user_type=UserType(user_type.upper()),
        )

        created_user = self._user_repository.create(user)
        return created_user


class RequestEmailVerificationRule:
    def __init__(
        self,
        verification_service: VerificationServiceAdapterInterface,
        cache_service: CacheServiceAdapterInterface,
        email_service: EmailServiceAdapterInterface,
    ) -> None:
        self._verification_service = verification_service
        self._cache_service = cache_service
        self._email_service = email_service

    def execute(self, user: User) -> None:
        if user.is_email_verified:
            raise BusinessRuleException("User account is already verified.")

        token = self._verification_service.generate_token()

        cache_key = f"email_verify_{str(user.uuid)}"
        self._cache_service.set(cache_key, (user.id, token))

        link = self._verification_service.generate_email_verification_link(
            user.uuid, token
        )

        self._email_service.send_verification_email(user.email, verification_link=link)


class VerifyEmailRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        email_service: EmailServiceAdapterInterface,
        verification_service: VerificationServiceAdapterInterface,
        cache_service: CacheServiceAdapterInterface,
    ) -> None:
        self._user_repository = user_repository
        self._email_service = email_service
        self._verification_service = verification_service
        self._cache_service = cache_service

    def execute(self, user_uuid: str, token: str) -> bool:
        cache_key = f"email_verify_{user_uuid}"

        cached_id, cached_token = self._cache_service.get(cache_key)

        user = self._user_repository.get_by_id(cached_id)

        if user.is_email_verified:
            return True

        if not user or str(user.uuid) != str(user_uuid) or cached_token != token:
            raise BusinessRuleException(
                "Provided user id or verification token is invalid."
            )

        user.is_email_verified = True
        self._user_repository.update(user)
        self._cache_service.delete(cache_key)

        return True


class LoginUserRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordServiceAdapterInterface,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service

    def execute(self, email: str, password: str) -> User:
        user = self._user_repository.get_by_email(email)

        if not user or not self._password_service.check(password, user.password_hash):
            raise BusinessRuleException("Provided email or password is invalid.")

        if not user.is_active:
            raise BusinessRuleException("Requested user account is deactivated.")

        if not user.is_email_verified:
            raise BusinessRuleException(
                "Requested user email is not verified. Please verify your email."
            )

        user.last_login = datetime.now(tz=UTC)

        updated_user = self._user_repository.update(user)
        return updated_user


class LogoutUserRule:
    def __init__(
        self,
        blacklisted_token_repository: BlackListedTokenRepositoryInterface,
        jwt_token_service: JWTTokenAdapterInterface,
    ) -> None:
        self._blacklisted_token_repository = blacklisted_token_repository
        self._jwt_token_service = jwt_token_service

    def execute(self, user_id: int, access_token: str) -> None:
        token_expiry = self._jwt_token_service.check_access_token_expiry(access_token)

        token = BlackListedToken(
            access=access_token, user_id=user_id, expires_at=token_expiry
        )
        self._blacklisted_token_repository.add(token)


class SocialAuthenticationRule:
    def __init__(
        self,
        social_authentication_service: SocialAuthenticationAdapterInterface,
        user_repository: UserRepositoryInterface | None = None,
    ) -> None:
        self._social_authentication_service = social_authentication_service
        self._user_repository = user_repository

    def begin_authentication(self, request: Any, user_type: str) -> Any:
        return self._social_authentication_service.begin(request, user_type=user_type)

    def complete_authentication(self, request: Any) -> Dict[str, str]:
        return self._user_repository.get_or_create_social(request)
