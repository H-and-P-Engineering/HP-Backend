from datetime import datetime, UTC
from typing import Any

from uuid6 import UUID
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from loguru import logger
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from social_core.actions import do_auth
from social_core.utils import (
    partial_pipeline_data,
    user_is_active,
    user_is_authenticated,
)

from core.exceptions import BadRequestError
from core.interfaces import IEmailService
from core.services import BaseCacheService
from core.tasks import invalidate_previous_session_task, update_user_data_task
from core.container import container
from .models import User, UserType
from .repositories import UserRepository, BlackListedTokenRepository


class UserCacheService(BaseCacheService):
    def __init__(self) -> None:
        super().__init__(prefix="user", timeout=settings.CACHE_USER_TIMEOUT)

    @staticmethod
    def _serialize(user: User) -> dict[str, Any]:
        return {
            "uuid": str(user.uuid),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "is_email_verified": user.is_email_verified,
            "is_active": user.is_active,
        }

    @staticmethod
    def _deserialize(data: dict[str, Any]) -> User:
        return User(
            uuid=UUID(data["uuid"]),
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=data["phone_number"],
            user_type=data["user_type"],
            is_email_verified=data["is_email_verified"],
            is_active=data["is_active"],
        )

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        cached = self.get(f"email:{email}")
        if not cached:
            logger.debug("Cache miss", key_type="email", key=email)
            return None

        return self._deserialize(cached)

    def get_by_uuid(self, user_uuid: UUID | str) -> dict[str, Any] | None:
        cached = self.get(f"uuid:{user_uuid}")
        if not cached:
            logger.debug("Cache miss", key_type="uuid", key=str(user_uuid))
            return None

        return self._deserialize(cached)

    def set_user(self, user: User) -> None:
        data = self._serialize(user)
        self.set(f"email:{user.email}", data)
        self.set(f"uuid:{user.uuid}", data)

    def invalidate(self, user: User) -> None:
        self.delete(f"email:{user.email}")
        self.delete(f"uuid:{user.uuid}")


class SocialCacheService(BaseCacheService):
    def __init__(self) -> None:
        super().__init__(prefix="social_auth", timeout=600)


class ActiveTokenCacheService(BaseCacheService):
    def __init__(self) -> None:
        timeout = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
        super().__init__(prefix="active_token", timeout=int(timeout))

    def get_active_token(self, user_id: int) -> str | None:
        return self.get(f"user:{user_id}")

    def set_active_token(self, user_id: int, token: str) -> None:
        self.set(f"user:{user_id}", token)

    def delete_active_token(self, user_id: int) -> None:
        self.delete(f"user:{user_id}")


class SocialAuthService:
    @staticmethod
    def begin_social_auth(request: Any) -> Any:
        return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)

    @staticmethod
    def get_or_create_social_user(request: Any) -> User:
        backend = request.backend
        user = request.user
        user_type = request.session.pop("user_type", UserType.BUYER.value)

        is_user_authenticated = user_is_authenticated(user)

        user = user if is_user_authenticated else None

        partial = partial_pipeline_data(backend, user)
        if partial:
            social_user = backend.continue_pipeline(partial, user_type=user_type)
            backend.clean_partial_pipeline(partial.token)
        else:
            social_user = backend.complete(user=user, user_type=user_type)

        if not social_user:
            raise AuthenticationFailed(
                "Social authentication failed. Requested user account is inactive"
            )

        if not user_is_active(social_user):
            raise AuthenticationFailed(
                "Social authentication failed. This account has been deactivated"
            )

        user_model = backend.strategy.storage.user.user_model()
        if social_user and not isinstance(social_user, user_model):
            raise AuthenticationFailed(
                "Social authentication failed. User object is invalid."
            )

        is_new_user = getattr(social_user, "is_new", False)
        logger.info(
            "Social authentication successful",
            user=str(social_user),
            is_new=is_new_user,
        )

        return social_user


class UserService:
    def __init__(
        self,
        cache: UserCacheService | None = None,
        email_service: IEmailService | None = None,
        repository: UserRepository | None = None,
    ) -> None:
        self.cache = cache or UserCacheService()
        self.email_service = email_service or container.email_service()
        self.repository = repository or container.user_repository()

    async def create(self, **kwargs: Any) -> User:
        user = await self.repository.create(**kwargs)
        self.cache.set_user(user)
        return user

    async def update(self, user_uuid: UUID | str, update_data: dict[str, Any]) -> None:
        logger.info(
            "Updating user", user_uuid=str(user_uuid), fields=list(update_data.keys())
        )
        await self.repository.update(user_uuid=user_uuid, update_data=update_data)

    async def fetch_user_for_verification(self, email: str) -> User:
        user = await self.repository.get_by_email(email=email)
        if not user:
            raise BadRequestError("User not found with the provided email.")
        if user.is_email_verified:
            raise BadRequestError("User is already verified.")
        return user

    async def verify_email(self, user_uuid: UUID | str) -> User:
        user = await self.repository.get_by_uuid(user_uuid)

        if user.is_email_verified:
            raise BadRequestError("Email already verified.")

        user = await self.repository.update_email_verification_status(user)
        self.cache.set_user(user)

        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.repository.get_by_email(email.lower())
        if not user:
            raise AuthenticationFailed("User with the provided email does not exist.")

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password.")

        if not user.is_email_verified:
            raise AuthenticationFailed("Email not verified. Please check your inbox.")

        if not user.is_active:
            raise AuthenticationFailed("User account is not active.")

        return user

    def send_email_verification(self, user: User) -> None:
        verification_link = container.verification_service().run(user.uuid)
        self.email_service.send_verification_email(user.email, verification_link)

    async def validate_and_verify_email(
        self, user_uuid: str, verification_token: str
    ) -> User:
        container.verification_service().validate_token(
            user_uuid=user_uuid,
            token=verification_token,
        )
        return await self.verify_email(user_uuid=user_uuid)


class AuthenticationService:
    def __init__(
        self,
        user_service: UserService | None = None,
        active_token_cache: ActiveTokenCacheService | None = None,
        blacklisted_token_repo: BlackListedTokenRepository | None = None,
        social_auth_service: SocialAuthService | None = None,
    ) -> None:
        self.user_service = user_service or container.user_service()
        self.active_token_cache = active_token_cache or ActiveTokenCacheService()
        self.blacklisted_token_repository = (
            blacklisted_token_repo or container.blacklisted_token_repository()
        )
        self.social_auth_service = (
            social_auth_service or container.social_auth_service()
        )

    async def login(self, email: str, password: str) -> tuple[User, dict[str, Any]]:
        user = await self.user_service.authenticate(email, password)

        invalidate_previous_session_task.delay(user.id)

        tokens = self._generate_tokens(user)
        self.active_token_cache.set_active_token(user.id, tokens["access"])

        return user, tokens

    def begin_social_auth(self, request: Any, user_type: str) -> Any:
        return self.social_auth_service.begin_social_auth(request)

    async def complete_authentication(
        self, request: Any
    ) -> tuple[User, dict[str, Any]]:
        user = self.social_auth_service.get_or_create_social_user(request)

        if user and not getattr(user, "is_new", False):
            data_to_update = {
                "last_login": datetime.now(tz=UTC),
            }
            if not user.is_email_verified:
                data_to_update["is_email_verified"] = True

            update_user_data_task.delay(user.uuid, data_to_update)
            self.user_service.cache.set_user(user)

        invalidate_previous_session_task.delay(user.id)

        tokens = self._generate_tokens(user)
        self.active_token_cache.set_active_token(user.id, tokens["access"])

        return user, tokens

    def orchestrate_social_login_response(
        self, user: User, tokens: dict[str, Any], user_data: dict[str, Any]
    ) -> dict[str, Any]:
        is_new_user = getattr(user, "is_new", False)
        session_id = container.verification_service().generate_token()

        response_data = {
            "user": user_data,
            **tokens,
            "message": (
                "Registration successful. Welcome to Housing & Properties!"
                if is_new_user
                else "Login successful. Welcome back!"
            ),
        }

        container.social_cache_service().set(session_id, response_data)

        frontend_url = (
            settings.FRONTEND_SIGNUP_URL if is_new_user else settings.FRONTEND_LOGIN_URL
        )

        redirect_url = None
        if frontend_url:
            redirect_url = f"{frontend_url}?is_new={is_new_user}"

        return {
            "session_id": session_id,
            "redirect_url": redirect_url,
            "response_data": response_data,
        }

    def verify_social_session_data(self, value: Any) -> bool:
        if not value:
            raise AuthenticationFailed(
                "Social authentication session is invalid or expired. Please try again."
            )

        return True

    def logout(self, user_id: int) -> None:
        invalidate_previous_session_task.delay(user_id)

    def _generate_tokens(self, user: User) -> dict[str, Any]:
        refresh = RefreshToken.for_user(user)
        tokens = {"refresh": str(refresh), "access": str(refresh.access_token)}
        return tokens
