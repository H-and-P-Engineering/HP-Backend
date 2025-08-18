from datetime import UTC, datetime
from typing import Any, Dict

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from social_core.actions import do_auth
from social_core.utils import partial_pipeline_data

from apps.authentication.application.ports import (
    JWTTokenAdapterInterface,
    PasswordServiceAdapterInterface,
    SocialAuthenticationAdapterInterface,
)
from apps.users.domain.models import User as DomainUser
from core.infrastructure.exceptions import BadRequestError


class DjangoPasswordServiceAdapter(PasswordServiceAdapterInterface):
    def hash(self, password: str) -> str:
        return make_password(password)

    def check(self, raw_password: str, hashed_password: str) -> bool:
        return check_password(raw_password, hashed_password)


class DjangoJWTTokenAdapter(JWTTokenAdapterInterface):
    def create_tokens(self, user) -> dict:
        refresh = RefreshToken.for_user(user)
        tokens = {"refresh": str(refresh), "access": str(refresh.access_token)}
        return tokens

    def check_access_token_expiry(self, access_token: str) -> datetime:
        try:
            access = AccessToken(access_token)
            expires_at = datetime.fromtimestamp(access.get("exp"), tz=UTC)
        except (TokenError, ExpiredTokenError, InvalidToken) as e:
            raise ValidationError("Access token is invalid.") from e
        return expires_at


class SocialAuthenticationAdapter(SocialAuthenticationAdapterInterface):
    def begin(self, request: Any, user_type: str) -> Any:
        return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)

    def get_or_create_social(self, request: Any) -> Dict[str, DomainUser | bool]:
        backend = request.backend
        user = request.user

        is_user_authenticated = getattr(user, "is_authenticated", False)
        user = user if is_user_authenticated else None

        partial = partial_pipeline_data(backend, user)
        if partial:
            social_user = backend.continue_pipeline(partial)
            backend.clean_partial_pipeline(partial.token)
        else:
            social_user = backend.complete(user=user)

        if not social_user:
            raise BadRequestError(
                "Social authentication failed. This account has been deactivated or does not exist."
            )

        if not getattr(social_user, "is_active", False):
            raise BadRequestError(
                "Social authentication failed. Requested user account is inactive."
            )

        user_model = backend.strategy.storage.user.user_model()
        if social_user and not isinstance(social_user, user_model):
            raise BadRequestError(
                "Social authentication failed. User object is invalid."
            )

        is_new_user = getattr(social_user, "is_new", False)

        return {"user": social_user, "is_new_user": is_new_user}
