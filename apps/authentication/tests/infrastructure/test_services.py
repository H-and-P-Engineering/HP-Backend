from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from django.contrib.auth.hashers import check_password as django_check_password
from faker import Faker
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import ExpiredTokenError, InvalidToken

from apps.authentication.infrastructure.services import (
    DjangoCacheServiceAdapter,
    DjangoEmailServiceAdapter,
    DjangoJWTTokenAdapter,
    DjangoPasswordServiceAdapter,
    DjangoVerificationServiceAdapter,
    SocialAuthenticationAdapter,
)
from apps.users.infrastructure.models import User as DjangoORMUser
from core.infrastructure.exceptions import BadRequestError, BaseAPIException


@pytest.fixture
def faker_instance():
    return Faker()


@pytest.fixture
def password_service() -> DjangoPasswordServiceAdapter:
    return DjangoPasswordServiceAdapter()


@pytest.fixture
def verification_service() -> DjangoVerificationServiceAdapter:
    return DjangoVerificationServiceAdapter()


@pytest.fixture
def cache_service() -> DjangoCacheServiceAdapter:
    return DjangoCacheServiceAdapter()


@pytest.fixture
def email_service() -> DjangoEmailServiceAdapter:
    return DjangoEmailServiceAdapter()


@pytest.fixture
def jwt_token_adapter() -> DjangoJWTTokenAdapter:
    return DjangoJWTTokenAdapter()


@pytest.fixture
def social_authentication_adapter() -> SocialAuthenticationAdapter:
    return SocialAuthenticationAdapter()


def test_password_service_hash_method(
    password_service: DjangoPasswordServiceAdapter, faker_instance: Faker
):
    raw_password = faker_instance.password()
    hashed_password = password_service.hash(raw_password)

    assert hashed_password != raw_password
    assert django_check_password(raw_password, hashed_password)


def test_password_service_check_method(
    password_service: DjangoPasswordServiceAdapter, faker_instance: Faker
):
    raw_password = faker_instance.password()
    hashed_password = password_service.hash(raw_password)

    assert password_service.check(raw_password, hashed_password) is True
    assert password_service.check("wrong_password", hashed_password) is False


def test_verification_service_generate_token(
    verification_service: DjangoVerificationServiceAdapter,
):
    token = verification_service.generate_token()
    assert isinstance(token, str)
    assert len(token) > 0


@patch("apps.authentication.infrastructure.services.reverse")
@patch("django.conf.settings.FROM_DOMAIN", "http://testserver")
def test_verification_service_generate_email_verification_link(
    mock_reverse: Mock,
    verification_service: DjangoVerificationServiceAdapter,
):
    test_uuid = uuid4()
    test_token = "test_verification_token"
    mock_reverse.return_value = (
        f"/api/v1/authentication/verify-email/{test_uuid}/{test_token}/"
    )

    link = verification_service.generate_email_verification_link(test_uuid, test_token)

    mock_reverse.assert_called_once_with(
        "authentication:verify-email",
        kwargs={
            "user_uuid": test_uuid,
            "verification_token": test_token,
        },
    )
    assert (
        link
        == f"http://testserver/api/v1/authentication/verify-email/{test_uuid}/{test_token}/"
    )


@patch("apps.authentication.infrastructure.services.cache")
def test_cache_service_get(mock_cache: Mock, cache_service: DjangoCacheServiceAdapter):
    mock_cache.get.return_value = "cached_value"
    result = cache_service.get("test_key")
    mock_cache.get.assert_called_once_with("test_key", None)
    assert result == "cached_value"


@patch("apps.authentication.infrastructure.services.cache")
@patch("django.conf.settings.DJANGO_CACHE_TIMEOUT", 900)
def test_cache_service_set_with_default_timeout(
    mock_cache: Mock, cache_service: DjangoCacheServiceAdapter
):
    cache_service.set("test_key", "test_value")
    mock_cache.set.assert_called_once_with("test_key", "test_value", 900)


@patch("apps.authentication.infrastructure.services.cache")
def test_cache_service_set_with_custom_timeout(
    mock_cache: Mock, cache_service: DjangoCacheServiceAdapter
):
    cache_service.set("test_key", "test_value", timeout=60)
    mock_cache.set.assert_called_once_with("test_key", "test_value", 60)


@patch("apps.authentication.infrastructure.services.cache")
def test_cache_service_delete(
    mock_cache: Mock, cache_service: DjangoCacheServiceAdapter
):
    cache_service.delete("test_key")
    mock_cache.delete.assert_called_once_with("test_key")


@patch("apps.authentication.infrastructure.services.cache")
def test_cache_service_delete_handles_exception(
    mock_cache: Mock, cache_service: DjangoCacheServiceAdapter
):
    mock_cache.delete.side_effect = Exception("Cache error")
    cache_service.delete("test_key")
    mock_cache.delete.assert_called_once_with("test_key")


@patch.object(DjangoEmailServiceAdapter, "_send_template_email")
@patch("django.conf.settings.DJANGO_VERIFICATION_TOKEN_EXPIRY", 15)
def test_email_service_send_verification_email_success(
    mock_send_template_email: Mock,
    email_service: DjangoEmailServiceAdapter,
    faker_instance: Faker,
):
    recipient_email = faker_instance.email()
    verification_link = "http://example.com/verify/123"

    email_service.send_verification_email(recipient_email, verification_link)

    mock_send_template_email.assert_called_once_with(
        subject="Verify your email address",
        template_name="verify_email",
        context={
            "email": recipient_email,
            "expiry_minutes": 15,
            "verification_link": verification_link,
        },
        recipient_list=[recipient_email],
    )


@patch.object(DjangoEmailServiceAdapter, "_send_template_email")
@patch("django.conf.settings.DEFAULT_FROM_EMAIL", "test@example.com")
def test_email_service_send_verification_email_handles_exception(
    mock_send_template_email: Mock,
    email_service: DjangoEmailServiceAdapter,
    faker_instance: Faker,
):
    recipient_email = faker_instance.email()
    verification_link = "http://example.com/verify/123"
    mock_send_template_email.side_effect = Exception("SMTP Error")

    with pytest.raises(BaseAPIException) as excinfo:
        email_service.send_verification_email(recipient_email, verification_link)

    assert "Failed to send verification email. Please try again later." in str(
        excinfo.value
    )
    mock_send_template_email.assert_called_once()


@patch("apps.authentication.infrastructure.services.render_to_string")
@patch("apps.authentication.infrastructure.services.strip_tags")
@patch("apps.authentication.infrastructure.services.EmailMultiAlternatives")
@patch("django.conf.settings.DEFAULT_FROM_EMAIL", "noreply@test.com")
def test_email_service_send_template_email_method_success(
    mock_email_multi_alternatives: Mock,
    mock_strip_tags: Mock,
    mock_render_to_string: Mock,
    email_service: DjangoEmailServiceAdapter,
    faker_instance: Faker,
):
    subject = "Test Subject"
    template_name = "test_template"
    context = {"key": "value"}
    recipient_list = [faker_instance.email()]

    mock_render_to_string.return_value = "<html>html content</html>"
    mock_strip_tags.return_value = "text content"
    mock_email_instance = Mock()
    mock_email_multi_alternatives.return_value = mock_email_instance
    mock_email_instance.send.return_value = 1

    result = email_service._send_template_email(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_list=recipient_list,
    )

    mock_render_to_string.assert_called_once_with(f"{template_name}.html", context)
    mock_strip_tags.assert_called_once_with("<html>html content</html>")
    mock_email_multi_alternatives.assert_called_once_with(
        subject=subject,
        body="text content",
        from_email="noreply@test.com",
        to=recipient_list,
    )
    mock_email_instance.attach_alternative.assert_called_once_with(
        "<html>html content</html>", "text/html"
    )
    mock_email_instance.send.assert_called_once()
    assert result == 1


@patch("rest_framework_simplejwt.tokens.RefreshToken.for_user")
def test_jwt_token_adapter_create_tokens(
    mock_refresh_token_for_user: Mock, jwt_token_adapter: DjangoJWTTokenAdapter
):
    mock_user = Mock(spec=DjangoORMUser)
    mock_refresh_token = Mock()
    mock_access_token = Mock()

    mock_refresh_token_for_user.return_value = mock_refresh_token
    mock_refresh_token.access_token = mock_access_token
    mock_refresh_token.__str__ = Mock(return_value="mock_refresh_token_string")
    mock_access_token.__str__ = Mock(return_value="mock_access_token_string")

    tokens = jwt_token_adapter.create_tokens(mock_user)

    mock_refresh_token_for_user.assert_called_once_with(mock_user)
    assert tokens == {
        "refresh": "mock_refresh_token_string",
        "access": "mock_access_token_string",
    }


@patch("apps.authentication.infrastructure.services.AccessToken")
def test_jwt_token_adapter_check_access_token_expiry_valid_token(
    mock_access_token_class: Mock, jwt_token_adapter: DjangoJWTTokenAdapter
):
    access_token_str = "valid_access_token"
    expected_expiry = datetime.now(tz=UTC) + timedelta(hours=1)

    mock_access_token_instance = Mock()
    mock_access_token_class.return_value = mock_access_token_instance

    mock_access_token_instance.get.return_value = expected_expiry.timestamp()

    expires_at = jwt_token_adapter.check_access_token_expiry(access_token_str)

    mock_access_token_class.assert_called_once_with(access_token_str)
    mock_access_token_instance.get.assert_called_once_with("exp")
    assert expires_at == expected_expiry


@patch("apps.authentication.infrastructure.services.AccessToken")
def test_jwt_token_adapter_check_access_token_expiry_invalid_token(
    mock_access_token_class: Mock, jwt_token_adapter: DjangoJWTTokenAdapter
):
    access_token_str = "invalid_access_token"

    mock_access_token_class.side_effect = InvalidToken("Token is invalid")

    with pytest.raises(ValidationError) as excinfo:
        jwt_token_adapter.check_access_token_expiry(access_token_str)

    assert "Access token is invalid." in str(excinfo.value)
    mock_access_token_class.assert_called_once_with(access_token_str)


@patch("apps.authentication.infrastructure.services.AccessToken")
def test_jwt_token_adapter_check_access_token_expiry_expired_token(
    mock_access_token_class: Mock, jwt_token_adapter: DjangoJWTTokenAdapter
):
    access_token_str = "expired_access_token"

    mock_access_token_class.side_effect = ExpiredTokenError("Token is expired")

    with pytest.raises(ValidationError) as excinfo:
        jwt_token_adapter.check_access_token_expiry(access_token_str)

    assert "Access token is invalid." in str(excinfo.value)
    mock_access_token_class.assert_called_once_with(access_token_str)


@patch("apps.authentication.infrastructure.services.do_auth")
def test_social_authentication_adapter_begin(
    mock_do_auth: Mock, social_authentication_adapter: SocialAuthenticationAdapter
):
    mock_request = Mock()
    mock_request.backend = Mock()
    mock_request.REDIRECT_FIELD_NAME = "next"
    mock_do_auth.return_value = "http://social_provider/auth"

    result = social_authentication_adapter.begin(mock_request, user_type="CLIENT")

    mock_do_auth.assert_called_once_with(
        mock_request.backend, redirect_name=mock_request.REDIRECT_FIELD_NAME
    )
    assert result == "http://social_provider/auth"


@patch("apps.authentication.infrastructure.services.partial_pipeline_data")
@patch("apps.authentication.infrastructure.services.DomainUser")
def test_social_authentication_adapter_get_or_create_social_existing_user(
    mock_domain_user: Mock,
    mock_partial_pipeline_data: Mock,
    social_authentication_adapter: SocialAuthenticationAdapter,
    faker_instance: Faker,
):
    """
    Test get_or_create_social when an existing user is returned by social_core.
    """
    mock_request = Mock()
    mock_request.backend = Mock()
    mock_request.user = Mock(is_authenticated=True, spec=DjangoORMUser)
    mock_request.user.is_authenticated = True

    existing_user_id = 123
    existing_email = faker_instance.email()
    mock_social_user = Mock(spec=DjangoORMUser)
    mock_social_user.id = existing_user_id
    mock_social_user.email = existing_email
    mock_social_user.is_active = True
    mock_social_user.is_new = False

    mock_partial_pipeline_data.return_value = None
    mock_request.backend.complete.return_value = mock_social_user
    mock_request.backend.strategy.storage.user.user_model.return_value = DjangoORMUser

    result = social_authentication_adapter.get_or_create_social(mock_request)

    mock_partial_pipeline_data.assert_called_once_with(
        mock_request.backend, mock_request.user
    )
    mock_request.backend.complete.assert_called_once_with(user=mock_request.user)
    assert result["user"] == mock_social_user
    assert result["is_new_user"] is False


@patch("apps.authentication.infrastructure.services.partial_pipeline_data")
@patch("apps.authentication.infrastructure.services.DomainUser")
def test_social_authentication_adapter_get_or_create_social_new_user(
    mock_domain_user: Mock,
    mock_partial_pipeline_data: Mock,
    social_authentication_adapter: SocialAuthenticationAdapter,
    faker_instance: Faker,
):
    mock_request = Mock()
    mock_request.backend = Mock()
    mock_request.user = Mock(is_authenticated=False)

    new_user_id = 456
    new_email = faker_instance.email()
    mock_social_user = Mock(spec=DjangoORMUser)
    mock_social_user.id = new_user_id
    mock_social_user.email = new_email
    mock_social_user.is_active = True
    mock_social_user.is_new = True

    mock_partial_pipeline_data.return_value = None
    mock_request.backend.complete.return_value = mock_social_user
    mock_request.backend.strategy.storage.user.user_model.return_value = DjangoORMUser

    result = social_authentication_adapter.get_or_create_social(mock_request)

    mock_partial_pipeline_data.assert_called_once_with(mock_request.backend, None)
    mock_request.backend.complete.assert_called_once_with(user=None)
    assert result["user"] == mock_social_user
    assert result["is_new_user"] is True


@patch("apps.authentication.infrastructure.services.partial_pipeline_data")
def test_social_authentication_adapter_get_or_create_social_inactive_user(
    mock_partial_pipeline_data: Mock,
    social_authentication_adapter: SocialAuthenticationAdapter,
):
    mock_request = Mock()
    mock_request.backend = Mock()
    mock_request.user = Mock(is_authenticated=False)

    mock_social_user = Mock()
    mock_social_user.is_active = False

    mock_partial_pipeline_data.return_value = None
    mock_request.backend.complete.return_value = mock_social_user

    with pytest.raises(BadRequestError) as excinfo:
        social_authentication_adapter.get_or_create_social(mock_request)

    assert "Social authentication failed. Requested user account is inactive." in str(
        excinfo.value
    )
    mock_partial_pipeline_data.assert_called_once_with(mock_request.backend, None)
    mock_request.backend.complete.assert_called_once_with(user=None)


@patch("apps.authentication.infrastructure.services.partial_pipeline_data")
def test_social_authentication_adapter_get_or_create_social_invalid_user_object(
    mock_partial_pipeline_data: Mock,
    social_authentication_adapter: SocialAuthenticationAdapter,
):
    mock_request = Mock()
    mock_request.backend = Mock()
    mock_request.user = Mock(is_authenticated=False)

    mock_social_user = Mock()
    mock_social_user.is_active = True

    mock_partial_pipeline_data.return_value = None
    mock_request.backend.complete.return_value = mock_social_user

    mock_request.backend.strategy.storage.user.user_model.return_value = DjangoORMUser

    with pytest.raises(BadRequestError) as excinfo:
        social_authentication_adapter.get_or_create_social(mock_request)

    assert "Social authentication failed. User object is invalid." in str(excinfo.value)
    mock_partial_pipeline_data.assert_called_once_with(mock_request.backend, None)
    mock_request.backend.complete.assert_called_once_with(user=None)
