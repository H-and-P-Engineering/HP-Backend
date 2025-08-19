from datetime import UTC, datetime
from typing import Any, Dict

from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from app.domain.users.entities import User as DomainUser


def create_jwt_tokens(user: DomainUser) -> Dict[str, Any]:
    refresh = RefreshToken.for_user(user)
    tokens = {"refresh": str(refresh), "access": str(refresh.access_token)}
    return tokens


def check_access_token_expiry(access_token: str) -> datetime:
    try:
        access = AccessToken(access_token)
        expires_at = datetime.fromtimestamp(access.get("exp"), tz=UTC)
    except (TokenError, ExpiredTokenError, InvalidToken) as e:
        raise ValidationError("Access token is invalid.") from e

    return expires_at
