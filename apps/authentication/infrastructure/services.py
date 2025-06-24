import re
import secrets
from datetime import UTC, datetime
from typing import Any, Dict, List

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from social_core.actions import do_auth

from apps.authentication.domain.models import UserType
from apps.authentication.domain.ports import (
    CacheServiceAdapterInterface,
    EmailServiceAdapterInterface,
    JWTTokenAdapterInterface,
    PasswordServiceAdapterInterface,
    SocialAuthenticationAdapterInterface,
    VerificationServiceAdapterInterface,
)
from core.infrastructure.exceptions import BadRequestError, BaseAPIException
from core.infrastructure.logging.base import logger


class DjangoPasswordServiceAdapter(PasswordServiceAdapterInterface):
    def validate(self, password):
        if " " in password:
            raise ValidationError(_("Password must not contain spaces."))

        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter.")
            )

        if not re.search(r"[a-z]", password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter.")
            )

        if not re.search(r"\d", password):
            raise ValidationError(_("Password must contain at least one digit."))

        if not re.search(r"[!@#$%^&*(),.?\"\'{}|<>]", password):
            raise ValidationError(
                _("Password must contain at least one special character.")
            )

    def hash(self, password):
        return make_password(password)

    def check(self, raw_password, hashed_password):
        return check_password(raw_password, hashed_password)


class DjangoVerificationServiceAdapter(VerificationServiceAdapterInterface):
    def generate_token(self):
        return secrets.token_urlsafe(32)

    def generate_email_verification_link(self, user_uuid, verification_token):
        path = reverse(
            "authentication:verify-email",
            kwargs={
                "user_uuid": user_uuid,
                "verification_token": verification_token,
            },
        )

        verification_url = f"{settings.FROM_DOMAIN}{path}"
        return verification_url


class DjangoCacheServiceAdapter(CacheServiceAdapterInterface):
    def get(self, key):
        cached_data = cache.get(key)
        if not cached_data:
            raise BadRequestError(_("Verification link is invalid or expired."))

        return cached_data

    def set(self, key, value, timeout=None):
        if not timeout:
            timeout = settings.DJANGO_CACHE_TIMEOUT

        cache.set(key, value, timeout)

    def delete(self, key):
        cache.delete(key)


class DjangoEmailServiceAdapter(EmailServiceAdapterInterface):
    def send_verification_email(self, recipient_email, verification_link):
        context = {
            "email": recipient_email,
            "expiry_minutes": settings.DJANGO_VERIFICATION_TOKEN_EXPIRY,
            "verification_link": verification_link,
        }

        try:
            self._send_template_email(
                subject="Verify your email address",
                template_name="verify_email",
                context=context,
                recipient_list=[recipient_email],
            )

        except Exception as e:
            logger.exception(
                f"Unknown error while sending verification email for '{recipient_email}': {e}"
            )
            raise BaseAPIException(
                _("Failed to send verification email. Try again later.")
            )

    def _send_template_email(
        self,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        recipient_list: List[str],
        from_email: str | None = None,
    ) -> int:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        html_content = render_to_string(f"{template_name}.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list,
        )
        email.attach_alternative(html_content, "text/html")
        return email.send()


class DjangoJWTTokenAdapter(JWTTokenAdapterInterface):
    def create_tokens(self, user):
        refresh = RefreshToken.for_user(user)

        tokens = {"refresh": refresh, "access": refresh.access_token}
        return tokens

    def check_access_token_expiry(self, access_token):
        access = AccessToken(access_token)

        try:
            expires_at = datetime.fromtimestamp(access.get("exp"), tz=UTC)
        except (TokenError, ExpiredTokenError, InvalidToken) as e:
            raise ValidationError(_("Access token is invalid.")) from e

        return expires_at


class SocialAuthenticationAdapter(SocialAuthenticationAdapterInterface):
    def begin(self, request: Request, user_type: str) -> Any:
        if user_type and user_type not in UserType.values():
            raise ValidationError(
                _("Social authentication failed. Provided user type is invalid.")
            )

        request.session["user_type"] = user_type
        request.session.save()

        return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)
