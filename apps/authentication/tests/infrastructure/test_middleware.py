from unittest.mock import Mock, patch

import pytest
from django.http import HttpRequest

from apps.authentication.infrastructure.middleware import TokenBlackListMiddleware
from apps.authentication.infrastructure.repositories import (
    DjangoBlackListedTokenRepository,
)
from core.infrastructure.logging.base import logger as base_logger


@pytest.fixture
def mock_get_response():
    """
    A mock for Django's get_response callable.
    """
    return Mock()


@pytest.fixture
def mock_blacklisted_token_repository() -> Mock:
    """
    A mock for the blacklisted token repository.
    """
    return Mock(spec=DjangoBlackListedTokenRepository)


@pytest.fixture
def token_blacklist_middleware(
    mock_get_response: Mock, mock_blacklisted_token_repository: Mock
):
    """
    Fixture for TokenBlackListMiddleware with mocked dependencies.
    """
    with patch(
        "apps.authentication.infrastructure.middleware.get_blacklisted_token_repository",
        return_value=mock_blacklisted_token_repository,
    ):
        middleware = TokenBlackListMiddleware(mock_get_response)
        yield middleware


@patch.object(base_logger, "warning")
def test_token_blacklist_middleware_blacklisted_token(
    mock_logger_warning: Mock,
    token_blacklist_middleware: TokenBlackListMiddleware,
    mock_blacklisted_token_repository: Mock,
):
    """
    Test that a blacklisted token is removed from the Authorization header.
    """
    request = HttpRequest()
    test_token = "blacklisted_jwt_token"
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {test_token}"

    mock_blacklisted_token_repository.exists.return_value = True

    response = token_blacklist_middleware.process_request(request)

    assert response is None
    assert request.META["HTTP_AUTHORIZATION"] == ""
    mock_blacklisted_token_repository.exists.assert_called_once_with(test_token)
    mock_logger_warning.assert_called_once_with(
        f"Blacklisted token ({test_token[:20]}...) attempted to access {str(request.path)}."
    )


@patch.object(base_logger, "warning")
def test_token_blacklist_middleware_not_blacklisted_token(
    mock_logger_warning: Mock,
    token_blacklist_middleware: TokenBlackListMiddleware,
    mock_blacklisted_token_repository: Mock,
):
    """
    Test that a non-blacklisted token is not removed from the Authorization header.
    """
    request = HttpRequest()
    test_token = "valid_jwt_token"
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {test_token}"

    mock_blacklisted_token_repository.exists.return_value = False

    response = token_blacklist_middleware.process_request(request)

    assert response is None
    assert request.META["HTTP_AUTHORIZATION"] == f"Bearer {test_token}"
    mock_blacklisted_token_repository.exists.assert_called_once_with(test_token)
    mock_logger_warning.assert_not_called()


@patch.object(base_logger, "warning")
def test_token_blacklist_middleware_no_authorization_header(
    mock_logger_warning: Mock,
    token_blacklist_middleware: TokenBlackListMiddleware,
    mock_blacklisted_token_repository: Mock,
):
    """
    Test that middleware does nothing if Authorization header is missing.
    """
    request = HttpRequest()

    response = token_blacklist_middleware.process_request(request)

    assert response is None
    assert "HTTP_AUTHORIZATION" not in request.META
    mock_blacklisted_token_repository.exists.assert_not_called()
    mock_logger_warning.assert_not_called()


@patch.object(base_logger, "warning")
def test_token_blacklist_middleware_invalid_authorization_format(
    mock_logger_warning: Mock,
    token_blacklist_middleware: TokenBlackListMiddleware,
    mock_blacklisted_token_repository: Mock,
):
    """
    Test that middleware does nothing if Authorization header format is invalid.
    """
    request = HttpRequest()
    request.META["HTTP_AUTHORIZATION"] = "Basic some_credentials"

    response = token_blacklist_middleware.process_request(request)

    assert response is None
    assert request.META["HTTP_AUTHORIZATION"] == "Basic some_credentials"
    mock_blacklisted_token_repository.exists.assert_not_called()
    mock_logger_warning.assert_not_called()
