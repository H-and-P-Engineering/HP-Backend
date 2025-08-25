from datetime import UTC, datetime
from typing import Any, Callable, Dict, Tuple

from app.application.users.ports import IUserRepository
from app.core.exceptions import BusinessRuleException
from app.domain.users.entities import User
from app.domain.users.enums import UserType
from app.infrastructure.authentication.models.tables import BlackListedToken


class RegisterUserRule:
    def __init__(
        self,
        user_repository: IUserRepository,
        hash_password: Callable[[Any], str],
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.user_repository = user_repository
        self.hash_password = hash_password
        self.event_publisher = event_publisher

    def __call__(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        user_type: str,
        event: Callable[[Any], Any] | None = None,
    ) -> User:
        password_hash = self.hash_password(password)

        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            user_type=UserType(
                user_type.upper() if isinstance(user_type, str) else user_type
            ),
            is_new=True,
        )

        created_user = self.user_repository.create(user)

        if event:
            self.event_publisher.publish(event(created_user.id))

        return created_user


class RequestEmailVerificationRule:
    def __init__(
        self,
        user_repository: IUserRepository,
        cache_service: Callable[[Any], Any],
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.cache_service = cache_service
        self.user_repository = user_repository
        self.event_publisher = event_publisher

    def __call__(
        self,
        email: str,
        user: User | None = None,
        event: Callable[[Any], Any] | None = None,
    ) -> None:
        if self.cache_service.get(f"{email}_verified"):
            raise BusinessRuleException(
                "Email verification request failed. User email is already verified."
            )

        user = user or self.user_repository.get_by_email(email)

        if not user:
            raise BusinessRuleException(
                "Email verification request failed. Provided email is invalid."
            )

        if user.is_email_verified:
            raise BusinessRuleException(
                "Email verification request failed. User email is already verified."
            )

        if event:
            self.event_publisher.publish(event(user.id))


class VerifyEmailRule:
    def __init__(
        self,
        user_repository: IUserRepository,
        cache_service: Callable[[Any], Any],
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.cache_service = cache_service
        self.user_repository = user_repository
        self.event_publisher = event_publisher

    def __call__(
        self, user_uuid: str, token: str, event: Callable[[Any], Any] | None = None
    ) -> Dict[str, Any]:
        cached_data = self.cache_service.get(f"email_verify_{user_uuid}")
        if cached_data:
            cached_id, cached_token = cached_data
        else:
            raise BusinessRuleException(
                "Email verification failed. Verification session is invalid or expired."
            )

        user = self.user_repository.get_by_id(cached_id)

        if user and user.is_email_verified:
            raise BusinessRuleException(
                "Email verification failed. User email is already verified."
            )

        if not user or str(user.uuid) != str(user_uuid) or cached_token != token:
            raise BusinessRuleException(
                "Email verification failed. Provided user id or verification token is invalid."
            )

        if event:
            self.event_publisher.publish(event(user.id))

        return {"user_type": user.user_type}


class LoginUserRule:
    def __init__(
        self,
        user_repository: IUserRepository,
        check_password: Callable[[Any], Any],
        create_jwt_tokens: Callable[[Any], Any],
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.user_repository = user_repository
        self.check_password = check_password
        self.create_jwt_tokens = create_jwt_tokens
        self.event_publisher = event_publisher

    def __call__(
        self, email: str, password: str, event: Callable[[Any], Any] | None = None
    ) -> Tuple[User, Dict[str, Any]]:
        user = self.user_repository.get_by_email(email)

        if not user or not self.check_password(password, user.password_hash):
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

        if event:
            self.event_publisher.publish(
                event(user.id, last_login=datetime.now(tz=UTC))
            )

        tokens = self.create_jwt_tokens(user)

        return user, tokens


class LogoutUserRule:
    def __init__(
        self,
        check_access_token_expiry: Callable[[Any], Any],
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.check_access_token_expiry = check_access_token_expiry
        self.event_publisher = event_publisher

    def __call__(
        self, user_id: int, access_token: str, event: Callable[[Any], Any]
    ) -> None:
        token_expiry = self.check_access_token_expiry(access_token)

        token = BlackListedToken(
            access=access_token, user_id=user_id, expires_at=token_expiry
        )

        if event:
            self.event_publisher.publish(event(user_id, token=token))


class SocialAuthenticationRule:
    def __init__(
        self,
        user_repository: IUserRepository,
        begin_social_auth: Callable[[Any], Any],
        create_jwt_tokens: Callable[[Any], Any],
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.user_repository = user_repository
        self.begin_social_auth = begin_social_auth
        self.create_jwt_tokens = create_jwt_tokens
        self.event_publisher = event_publisher

    def begin_authentication(self, request: Any, user_type: str) -> Any:
        return self.begin_social_auth(request, user_type=user_type)

    def complete_authentication(
        self, request: Any, event: Callable[[Any], Any]
    ) -> Tuple[Any, Dict[str, Any]]:
        user = self.user_repository.get_or_create_social_user(request)
        if user and not user.is_new and event:
            kwargs: Dict[str, Any] = {"last_login": datetime.now(tz=UTC)}

            if not user.is_email_verified:
                kwargs["is_email_verified"] = True

            self.event_publisher.publish(event(user.id, **kwargs))

        tokens = self.create_jwt_tokens(user)

        return user, tokens
