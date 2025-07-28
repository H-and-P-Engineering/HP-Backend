from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from apps.authentication.domain.events import (
    UserEmailVerifiedEvent,
    UserLogoutEvent,
    UserUpdateEvent,
    UserVerificationEmailEvent,
)
from apps.authentication.domain.models import BlackListedToken as DomainBlackListedToken
from apps.authentication.infrastructure.event_handlers import (
    blacklist_jwt_token,
    cache_email_verification_status,
    send_verification_email_event,
    update_user_details,
    update_user_verification_status,
)
from apps.authentication.infrastructure.repositories import (
    DjangoBlackListedTokenRepository,
)
from apps.authentication.infrastructure.services import (
    DjangoCacheServiceAdapter,
    DjangoEmailServiceAdapter,
    DjangoVerificationServiceAdapter,
)
from apps.users.domain.models import User as DomainUser
from apps.users.infrastructure.repositories import DjangoUserRepository


@pytest.fixture
def mock_user_repository() -> Mock:
    return Mock(spec=DjangoUserRepository)


@pytest.fixture
def mock_verification_service() -> Mock:
    return Mock(spec=DjangoVerificationServiceAdapter)


@pytest.fixture
def mock_cache_service() -> Mock:
    return Mock(spec=DjangoCacheServiceAdapter)


@pytest.fixture
def mock_email_service() -> Mock:
    return Mock(spec=DjangoEmailServiceAdapter)


@pytest.fixture
def mock_blacklisted_token_repository() -> Mock:
    return Mock(spec=DjangoBlackListedTokenRepository)


def test_send_verification_email_event(
    mock_user_repository: Mock,
    mock_verification_service: Mock,
    mock_cache_service: Mock,
    mock_email_service: Mock,
):
    user_id = 1
    user_uuid = uuid4()
    user_email = "test@example.com"
    mock_user = DomainUser(
        id=user_id, uuid=user_uuid, email=user_email, is_email_verified=False
    )
    verification_token = "generated_token"
    verification_link = "http://example.com/verify/link"

    event = UserVerificationEmailEvent(user_id=user_id)

    mock_user_repository.get_by_id.return_value = mock_user
    mock_verification_service.generate_token.return_value = verification_token
    mock_verification_service.generate_email_verification_link.return_value = (
        verification_link
    )

    send_verification_email_event(
        event,
        mock_user_repository,
        mock_verification_service,
        mock_cache_service,
        mock_email_service,
    )

    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_verification_service.generate_token.assert_called_once()
    mock_cache_service.set.assert_called_once_with(
        f"email_verify_{str(user_uuid)}", (user_id, verification_token)
    )
    mock_verification_service.generate_email_verification_link.assert_called_once_with(
        user_uuid, verification_token
    )
    mock_email_service.send_verification_email.assert_called_once_with(
        user_email, verification_link=verification_link
    )


def test_cache_email_verification_status(
    mock_user_repository: Mock, mock_cache_service: Mock
):
    user_id = 1
    user_uuid = uuid4()
    user_email = "verified_user@example.com"
    mock_user = DomainUser(
        id=user_id, uuid=user_uuid, email=user_email, is_email_verified=True
    )

    event = UserEmailVerifiedEvent(user_id=user_id)

    mock_user_repository.get_by_id.return_value = mock_user

    cache_email_verification_status(event, mock_user_repository, mock_cache_service)

    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_cache_service.delete.assert_called_once_with(f"email_verify_{user_uuid}")
    mock_cache_service.set.assert_called_once_with(
        f"{user_email}_verified", str(user_email)
    )


def test_update_user_verification_status(mock_user_repository: Mock):
    user_id = 1
    mock_user = DomainUser(
        id=user_id, email="user@example.com", is_email_verified=False
    )

    event = UserEmailVerifiedEvent(user_id=user_id)

    mock_user_repository.get_by_id.return_value = mock_user

    update_user_verification_status(event, mock_user_repository)

    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_user_repository.update.assert_called_once_with(
        mock_user, is_email_verified=True
    )


def test_update_user_details(mock_user_repository: Mock):
    user_id = 1
    user_email = "existing@example.com"
    mock_user = DomainUser(
        id=user_id, email=user_email, first_name="Old", last_name="User"
    )
    update_fields = {"first_name": "New", "last_name": "Name"}

    event = UserUpdateEvent(user_id=user_id, update_fields=update_fields)

    mock_user_repository.get_by_id.return_value = mock_user

    update_user_details(event, mock_user_repository)

    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_user_repository.update.assert_called_once_with(mock_user, **update_fields)


def test_blacklist_jwt_token(mock_blacklisted_token_repository: Mock):
    user_id = 123
    access_token = "test_jwt_access_token"
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=30)

    domain_blacklisted_token = DomainBlackListedToken(
        access=access_token,
        user_id=user_id,
        expires_at=expires_at,
    )

    event = UserLogoutEvent(token=domain_blacklisted_token, user_id=user_id)

    blacklist_jwt_token(event, mock_blacklisted_token_repository)

    mock_blacklisted_token_repository.add.assert_called_once_with(
        domain_blacklisted_token
    )
