from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .email import EmailService

if TYPE_CHECKING:
    from authentication.models import User as UserType

import re
from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import authenticate

from core.exceptions import BadRequestError
from core.logging import logger

User = get_user_model()


class AuthenticationService:
    """
    Service class for authentication operations.

    This service handles:
    - User registration with profile creation
    - Authentication and token generation
    - Password management
    - Email verification
    """

    def register_user(
        self, email: str, password: str, first_name: str, last_name: str, user_type: str
    ) -> tuple["UserType", dict[str, str]]:
        """Register a new user with appropriate profile creation."""

        self._validate_password(password)

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                user_type=user_type,
                first_name=first_name,
                last_name=last_name,
            )

            tokens = self._generate_authentication_tokens(user)

            self._send_verification_email(user)

            return user, tokens

        except Exception as e:
            raise e

    def login(self, email: str, password: str) -> tuple["UserType", dict[str, str]]:
        """Authenticate user and generate tokens."""

        user = authenticate(username=email, password=password)
        if not user:
            raise ValidationError(_("Invalid email or password"))

        if not user.is_active:
            raise BadRequestError("Requested user account is deactivated")

        if not user.is_email_verified:
            raise BadRequestError(
                _("Requested user email is not verified. Please verify your email")
            )

        tokens = self._generate_authentication_tokens(user)

        return user, tokens

    def verify_email(self, user_id: str, token: str) -> bool:
        """Verify user's email address."""

        cache_key = f"email_verify_{user_id}"

        try:
            cached_id, cached_token = cache.get(cache_key)
        except Exception as e:
            logger.exception(e)
            raise ValidationError(_("Invalid or expired verification token")) from e

        user = User.objects.get(id=cached_id)
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        cache.delete(cache_key)

        return True

    def begin_social_authentication(
        self, request: Any, backend: str, user_type: str
    ) -> Any:
        """Begin the social authentication process."""

        from django.contrib.auth import REDIRECT_FIELD_NAME
        from social_core.actions import do_auth

        if user_type and user_type not in User.UserType.values:
            raise ValidationError(_("Invalid user type"))

        request.session["user_type"] = user_type
        request.session.save()

        return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)

    def complete_social_authentication(self, request, backend):
        """
        Complete the social authentication process.

        Handles both partial and full pipeline completion, generates tokens for the user.
        """

        from social_core.utils import (
            partial_pipeline_data,
            user_is_active,
            user_is_authenticated,
        )

        backend = request.backend
        user = request.user
        user_type = request.session.get("user_type", User.UserType.CLIENT)

        if "user_type" in request.session:
            del request.session["user_type"]

        is_user_authenticated = user_is_authenticated(user)
        user = user if is_user_authenticated else None

        partial = partial_pipeline_data(backend, user)
        if partial:
            user = backend.continue_pipeline(partial, user_type=user_type)
            backend.clean_partial_pipeline(partial.token)
        else:
            user = backend.complete(user=user, user_type=user_type)

        user_model = backend.strategy.storage.user.user_model()
        if user and not isinstance(user, user_model):
            raise BadRequestError(
                _("Social authentication failed. Invalid User object.")
            )

        if not user:
            raise BadRequestError(_("Requested user account is inactive"))

        if not user_is_active(user):
            raise BadRequestError(_("This account has been deactivated"))

        tokens = self._generate_authentication_tokens(user)

        return user, tokens

    def _validate_password(self, password: str) -> None:
        """
        Validate password strength.

        Ensures the password contains at least one uppercase letter, one lowercase letter,
        one digit, one special character, and no spaces.
        """
        if " " in password:
            raise ValidationError({"password": "Password must not contain spaces."})

        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                {
                    "password": "Ensure this field contains at least one uppercase letter."
                }
            )

        if not re.search(r"[a-z]", password):
            raise ValidationError(
                {
                    "password": "Ensure this field contains at least one lowercase letter."
                }
            )

        if not re.search(r"\d", password):
            raise ValidationError(
                {"password": "Ensure this field contains at least one digit."}
            )

        if not re.search(r"[^\w\s]", password):
            raise ValidationError(
                {
                    "password": "Ensure this field contains at least one special character."
                }
            )

    def _generate_authentication_tokens(self, user: "UserType") -> dict[str, str]:
        """Generate JWT tokens for users."""

        refresh = RefreshToken.for_user(user)
        refresh["user_type"] = user.user_type
        refresh["email"] = user.email

        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    def _send_verification_email(self, user: "UserType") -> None:
        """Send email verification link."""

        token = self._generate_verification_token()

        cache_key = f"email_verify_{str(user.uuid)}"

        expiry = getattr(settings, "VERIFICATION_TOKEN_EXPIRY", 15)
        cache.set(cache_key, (user.id, token), expiry * 60)

        EmailService.send_verification_email(user, token, expiry)

    def _generate_verification_token(self) -> str:
        """Generate secure verification token."""

        import secrets

        return secrets.token_urlsafe(32)
