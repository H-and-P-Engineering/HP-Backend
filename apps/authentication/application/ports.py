from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from apps.authentication.domain.models import BlackListedToken as DomainBlackListedToken
from apps.users.domain.models import User as DomainUser


class PasswordServiceAdapterInterface(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        pass

    @abstractmethod
    def check(self, raw_password: str, hashed_password: str) -> bool:
        pass


class JWTTokenAdapterInterface(ABC):
    @abstractmethod
    def create_tokens(self, user: ...) -> Dict[str, Any]:
        pass

    @abstractmethod
    def check_access_token_expiry(self, access_token: str) -> datetime:
        pass


class CacheServiceAdapterInterface(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass


class EmailServiceAdapterInterface(ABC):
    @abstractmethod
    def send_verification_email(
        self, recipient_email: str, verification_link: str
    ) -> None:
        pass


class VerificationServiceAdapterInterface(ABC):
    @abstractmethod
    def generate_token(self) -> str:
        pass

    @abstractmethod
    def generate_email_verification_link(
        self, user_uuid: UUID, verification_token: str
    ) -> str:
        pass


class BlackListedTokenRepositoryInterface(ABC):
    @abstractmethod
    def add(self, blacklisted_token: DomainBlackListedToken) -> DomainBlackListedToken:
        pass

    @abstractmethod
    def exists(self, jti: str) -> bool:
        pass


class SocialAuthenticationAdapterInterface(ABC):
    @abstractmethod
    def begin(self, request: Any, user_type: str) -> Any:
        pass


class EventPublisherInterface(ABC):
    @abstractmethod
    def publish(self, event: Any) -> None:
        pass
