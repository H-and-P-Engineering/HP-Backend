from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from apps.authentication.domain.models import BlackListedToken as DomainBlackListedToken


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
