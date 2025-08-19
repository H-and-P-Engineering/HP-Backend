from typing import Protocol

from app.domain.authentication.entities import BlackListedToken


class IBlackListedTokenRepository(Protocol):
    def create(self, blacklisted_token: BlackListedToken) -> BlackListedToken: ...

    def check_exists(self, jti: str) -> bool: ...
