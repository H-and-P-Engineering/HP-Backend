import random
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from faker import Faker

from apps.authentication.application.ports import (
    CacheServiceAdapterInterface,
    EventPublisherInterface,
    JWTTokenAdapterInterface,
    PasswordServiceAdapterInterface,
    SocialAuthenticationAdapterInterface,
)
from apps.authentication.application.rules import (
    LoginUserRule,
    LogoutUserRule,
    RegisterUserRule,
    RequestEmailVerificationRule,
    SocialAuthenticationRule,
    UpdateUserTypeRule,
    VerifyEmailRule,
)
from apps.authentication.domain.models import BlackListedToken
from apps.users.application.ports import UserRepositoryInterface
from apps.users.domain.models import User as DomainUser
from core.application.exceptions import BusinessRuleException


@pytest.fixture
def mock_user_repository() -> Mock:
    return Mock(spec=UserRepositoryInterface)


@pytest.fixture
def faker_instance() -> Faker:
    return Faker()


@pytest.fixture
def mock_password_service() -> Mock:
    return Mock(spec=PasswordServiceAdapterInterface)


@pytest.fixture
def mock_event_publisher() -> Mock:
    return Mock(spec=EventPublisherInterface)


@pytest.fixture
def mock_cache_service() -> Mock:
    return Mock(spec=CacheServiceAdapterInterface)


@pytest.fixture
def mock_jwt_token_service() -> Mock:
    return Mock(spec=JWTTokenAdapterInterface)


@pytest.fixture
def mock_social_authentication_service() -> Mock:
    return Mock(spec=SocialAuthenticationAdapterInterface)


@pytest.fixture
def register_user_rule(
    mock_user_repository: Mock,
    mock_password_service: Mock,
    mock_event_publisher: Mock,
) -> RegisterUserRule:
    return RegisterUserRule(
        user_repository=mock_user_repository,
        password_service=mock_password_service,
        event_publisher=mock_event_publisher,
    )


@pytest.fixture
def login_user_rule(
    mock_user_repository: Mock,
    mock_password_service: Mock,
    mock_event_publisher: Mock,
) -> LoginUserRule:
    return LoginUserRule(
        user_repository=mock_user_repository,
        password_service=mock_password_service,
        event_publisher=mock_event_publisher,
    )


@pytest.fixture
def request_email_verification_rule(
    mock_cache_service: Mock,
    mock_event_publisher: Mock,
    mock_user_repository: Mock,
) -> RequestEmailVerificationRule:
    return RequestEmailVerificationRule(
        cache_service=mock_cache_service,
        event_publisher=mock_event_publisher,
        user_repository=mock_user_repository,
    )


@pytest.fixture
def verify_email_rule(
    mock_cache_service: Mock,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
) -> VerifyEmailRule:
    return VerifyEmailRule(
        cache_service=mock_cache_service,
        user_repository=mock_user_repository,
        event_publisher=mock_event_publisher,
    )


@pytest.fixture
def logout_user_rule(
    mock_jwt_token_service: Mock,
    mock_event_publisher: Mock,
) -> LogoutUserRule:
    return LogoutUserRule(
        jwt_token_service=mock_jwt_token_service,
        event_publisher=mock_event_publisher,
    )


@pytest.fixture
def social_authentication_rule(
    mock_social_authentication_service: Mock,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
) -> SocialAuthenticationRule:
    return SocialAuthenticationRule(
        social_authentication_service=mock_social_authentication_service,
        user_repository=mock_user_repository,
        event_publisher=mock_event_publisher,
    )


@pytest.fixture
def update_user_type_rule(
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
) -> UpdateUserTypeRule:
    return UpdateUserTypeRule(
        user_repository=mock_user_repository,
        event_publisher=mock_event_publisher,
    )


def test_register_user_rule_success(
    register_user_rule: RegisterUserRule,
    mock_user_repository: Mock,
    mock_password_service: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()
    password = faker_instance.password()
    first_name = faker_instance.first_name()
    last_name = faker_instance.last_name()
    phone_number = faker_instance.phone_number()
    user_type = random.choice(["CLIENT", "VENDOR", "AGENT", "SERVICE_PROVIDER"])
    hashed_password = faker_instance.pystr()

    mock_password_service.hash.return_value = hashed_password
    mock_user_repository.create.return_value = DomainUser(
        id=1,
        email=email,
        password_hash=hashed_password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        user_type=user_type,
        uuid=faker_instance.uuid4(),
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    created_user = register_user_rule.execute(
        email, password, first_name, last_name, phone_number, user_type
    )

    mock_password_service.hash.assert_called_once_with(password)
    mock_user_repository.create.assert_called_once()

    called_user_arg = mock_user_repository.create.call_args[0][0]

    assert called_user_arg.email == email
    assert called_user_arg.password_hash == hashed_password
    assert called_user_arg.first_name == first_name
    assert called_user_arg.last_name == last_name

    mock_event_publisher.publish.assert_called_once()

    published_event = mock_event_publisher.publish.call_args[0][0]

    assert published_event.__class__.__name__ == "UserVerificationEmailEvent"
    assert published_event.user_id == created_user.id

    assert created_user.email == email
    assert created_user.first_name == first_name
    assert created_user.last_name == last_name


def test_login_user_rule_success(
    login_user_rule: LoginUserRule,
    mock_user_repository: Mock,
    mock_password_service: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()
    password = faker_instance.password()
    hashed_password = f"hashed_{password}"

    mock_user = DomainUser(
        id=1,
        email=email,
        password_hash=hashed_password,
        is_active=True,
        is_email_verified=True,
    )

    mock_user_repository.get_by_email.return_value = mock_user
    mock_password_service.check.return_value = True

    logged_in_user = login_user_rule.execute(email, password)

    mock_user_repository.get_by_email.assert_called_once_with(email)
    mock_password_service.check.assert_called_once_with(password, hashed_password)
    mock_event_publisher.publish.assert_called_once()

    published_event = mock_event_publisher.publish.call_args[0][0]

    assert published_event.__class__.__name__ == "UserUpdateEvent"
    assert published_event.user_id == mock_user.id
    assert "last_login" in published_event.update_fields
    assert logged_in_user.email == email
    assert logged_in_user.id == mock_user.id


def test_request_email_verification_rule_success(
    request_email_verification_rule: RequestEmailVerificationRule,
    mock_cache_service: Mock,
    mock_event_publisher: Mock,
    mock_user_repository: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()
    mock_user = DomainUser(id=2, email=email, is_email_verified=False)

    mock_cache_service.get.return_value = None
    mock_user_repository.get_by_email.return_value = mock_user

    request_email_verification_rule.execute(email)

    mock_cache_service.get.assert_called_once_with(f"{email}_verified")
    mock_user_repository.get_by_email.assert_called_once_with(email)
    mock_event_publisher.publish.assert_called_once()

    published_event = mock_event_publisher.publish.call_args[0][0]

    assert published_event.__class__.__name__ == "UserVerificationEmailEvent"
    assert published_event.user_id == mock_user.id


def test_request_email_verification_rule_already_verified_cached(
    request_email_verification_rule: RequestEmailVerificationRule,
    mock_cache_service: Mock,
    mock_event_publisher: Mock,
    mock_user_repository: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()

    mock_cache_service.get.return_value = True

    with pytest.raises(BusinessRuleException) as excinfo:
        request_email_verification_rule.execute(email)

    assert "Email verification request failed. User email is already verified." in str(
        excinfo.value
    )

    mock_cache_service.get.assert_called_once_with(f"{email}_verified")
    mock_user_repository.get_by_email.assert_not_called()
    mock_event_publisher.publish.assert_not_called()


def test_request_email_verification_rule_already_verified_user_object(
    request_email_verification_rule: RequestEmailVerificationRule,
    mock_cache_service: Mock,
    mock_event_publisher: Mock,
    mock_user_repository: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()
    mock_user = DomainUser(id=3, email=email, is_email_verified=True)

    mock_cache_service.get.return_value = None
    mock_user_repository.get_by_email.return_value = mock_user

    with pytest.raises(BusinessRuleException) as excinfo:
        request_email_verification_rule.execute(email)

    assert "Email verification request failed. User email is already verified." in str(
        excinfo.value
    )
    mock_cache_service.get.assert_called_once_with(f"{email}_verified")
    mock_user_repository.get_by_email.assert_called_once_with(email)
    mock_event_publisher.publish.assert_called_once()

    published_event = mock_event_publisher.publish.call_args[0][0]

    assert published_event.__class__.__name__ == "UserEmailVerifiedEvent"
    assert published_event.user_id == mock_user.id


def test_request_email_verification_rule_non_existent_user(
    request_email_verification_rule: RequestEmailVerificationRule,
    mock_cache_service: Mock,
    mock_event_publisher: Mock,
    mock_user_repository: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()

    mock_cache_service.get.return_value = None
    mock_user_repository.get_by_email.return_value = None

    with pytest.raises(BusinessRuleException) as excinfo:
        request_email_verification_rule.execute(email)

    assert "Email verification request failed. Provided email is invalid." in str(
        excinfo.value
    )

    mock_cache_service.get.assert_called_once_with(f"{email}_verified")
    mock_user_repository.get_by_email.assert_called_once_with(email)
    mock_event_publisher.publish.assert_not_called()


def test_verify_email_rule_success(
    verify_email_rule: VerifyEmailRule,
    mock_cache_service: Mock,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    user_id = 1
    user_uuid = faker_instance.uuid4()
    email = faker_instance.email()
    token = "valid_token"
    mock_user = DomainUser(
        id=user_id, uuid=user_uuid, email=email, is_email_verified=False
    )

    mock_cache_service.get.return_value = (user_id, token)
    mock_user_repository.get_by_id.return_value = mock_user

    verify_email_rule.execute(str(user_uuid), token)

    mock_cache_service.get.assert_called_once_with(f"email_verify_{user_uuid}")
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_event_publisher.publish.assert_called_once()

    published_event = mock_event_publisher.publish.call_args[0][0]

    assert published_event.__class__.__name__ == "UserEmailVerifiedEvent"
    assert published_event.user_id == user_id


def test_verify_email_rule_invalid_or_expired_session(
    verify_email_rule: VerifyEmailRule,
    mock_cache_service: Mock,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    user_uuid = faker_instance.uuid4()
    token = "some_token"

    mock_cache_service.get.return_value = None

    with pytest.raises(BusinessRuleException) as excinfo:
        verify_email_rule.execute(str(user_uuid), token)

    assert (
        "Email verification failed. Verification session is invalid or expired."
        in str(excinfo.value)
    )

    mock_cache_service.get.assert_called_once_with(f"email_verify_{user_uuid}")
    mock_user_repository.get_by_id.assert_not_called()
    mock_event_publisher.publish.assert_not_called()


def test_verify_email_rule_already_verified_user(
    verify_email_rule: VerifyEmailRule,
    mock_cache_service: Mock,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    user_id = 2
    user_uuid = faker_instance.uuid4()
    email = faker_instance.email()
    token = "valid_token"
    mock_user = DomainUser(
        id=user_id, uuid=user_uuid, email=email, is_email_verified=True
    )

    mock_cache_service.get.return_value = (user_id, token)
    mock_user_repository.get_by_id.return_value = mock_user

    with pytest.raises(BusinessRuleException) as excinfo:
        verify_email_rule.execute(str(user_uuid), token)

    assert "Email verification failed. User email is already verified." in str(
        excinfo.value
    )

    mock_cache_service.get.assert_called_once_with(f"email_verify_{user_uuid}")
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_event_publisher.publish.assert_not_called()


def test_verify_email_rule_invalid_user_id_or_token(
    verify_email_rule: VerifyEmailRule,
    mock_cache_service: Mock,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    user_id = 3
    user_uuid = faker_instance.uuid4()
    email = faker_instance.email()
    correct_token = "correct_token"
    incorrect_token = "incorrect_token"
    mock_user = DomainUser(
        id=user_id, uuid=user_uuid, email=email, is_email_verified=False
    )

    mock_cache_service.get.return_value = (user_id, correct_token)
    mock_user_repository.get_by_id.return_value = None

    with pytest.raises(BusinessRuleException) as excinfo:
        verify_email_rule.execute(str(user_uuid), correct_token)

    assert (
        "Email verification failed. Provided user id or verification token is invalid."
        in str(excinfo.value)
    )

    mock_cache_service.get.assert_called_once_with(f"email_verify_{user_uuid}")
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_event_publisher.publish.assert_not_called()

    mock_cache_service.reset_mock()
    mock_user_repository.reset_mock()
    mock_event_publisher.reset_mock()

    mock_cache_service.get.return_value = (user_id, correct_token)
    mock_user_repository.get_by_id.return_value = DomainUser(
        id=user_id, uuid=faker_instance.uuid4(), email=email, is_email_verified=False
    )

    with pytest.raises(BusinessRuleException) as excinfo:
        verify_email_rule.execute(str(user_uuid), correct_token)

    assert (
        "Email verification failed. Provided user id or verification token is invalid."
        in str(excinfo.value)
    )

    mock_cache_service.get.assert_called_once_with(f"email_verify_{user_uuid}")
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_event_publisher.publish.assert_not_called()

    mock_cache_service.reset_mock()
    mock_user_repository.reset_mock()
    mock_event_publisher.reset_mock()

    mock_cache_service.get.return_value = (user_id, correct_token)
    mock_user_repository.get_by_id.return_value = mock_user

    with pytest.raises(BusinessRuleException) as excinfo:
        verify_email_rule.execute(str(user_uuid), incorrect_token)

    assert (
        "Email verification failed. Provided user id or verification token is invalid."
        in str(excinfo.value)
    )

    mock_cache_service.get.assert_called_once_with(f"email_verify_{user_uuid}")
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_event_publisher.publish.assert_not_called()


def test_logout_user_rule_success(
    logout_user_rule: LogoutUserRule,
    mock_jwt_token_service: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    user_id = 123
    access_token = faker_instance.pystr()
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=30)

    mock_jwt_token_service.check_access_token_expiry.return_value = expires_at

    logout_user_rule.execute(user_id, access_token)

    mock_jwt_token_service.check_access_token_expiry.assert_called_once_with(
        access_token
    )
    mock_event_publisher.publish.assert_called_once()

    published_event = mock_event_publisher.publish.call_args[0][0]
    assert published_event.__class__.__name__ == "UserLogoutEvent"
    assert published_event.user_id == user_id
    assert isinstance(published_event.token, BlackListedToken)
    assert published_event.token.access == access_token
    assert published_event.token.user_id == user_id
    assert published_event.token.expires_at == expires_at


def test_social_authentication_rule_begin_authentication(
    social_authentication_rule: SocialAuthenticationRule,
    mock_social_authentication_service: Mock,
):
    mock_request = Mock()
    mock_social_authentication_service.begin.return_value = "redirect_url"

    result = social_authentication_rule.begin_authentication(
        mock_request, user_type="CLIENT"
    )

    mock_social_authentication_service.begin.assert_called_once_with(
        mock_request, user_type="CLIENT"
    )
    assert result == "redirect_url"


def test_social_authentication_rule_complete_authentication(
    social_authentication_rule: SocialAuthenticationRule,
    mock_user_repository: Mock,
    faker_instance: Faker,
):
    mock_request = Mock()
    mock_user_data = DomainUser(
        email=faker_instance.email(),
        password_hash=faker_instance.pystr(),
        first_name=faker_instance.first_name(),
        last_name=faker_instance.last_name(),
    )
    mock_user_repository.get_or_create_social.return_value = mock_user_data

    result = social_authentication_rule.complete_authentication(mock_request)

    mock_user_repository.get_or_create_social.assert_called_once_with(mock_request)
    assert result == mock_user_data


def test_update_user_type_rule_success(
    update_user_type_rule: UpdateUserTypeRule,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()
    user_type = "AGENT"
    mock_user = DomainUser(id=1, email=email, is_active=True, is_email_verified=True)

    mock_user_repository.get_by_email.return_value = mock_user

    update_user_type_rule.execute(email, user_type)

    mock_user_repository.get_by_email.assert_called_once_with(email)
    mock_event_publisher.publish.assert_called_once()

    published_event = mock_event_publisher.publish.call_args[0][0]
    assert published_event.__class__.__name__ == "UserUpdateEvent"
    assert published_event.user_id == mock_user.id
    assert published_event.update_fields == {"user_type": user_type}


def test_update_user_type_rule_non_existent_user(
    update_user_type_rule: UpdateUserTypeRule,
    mock_user_repository: Mock,
    mock_event_publisher: Mock,
    faker_instance: Faker,
):
    email = faker_instance.email()
    user_type = "AGENT"

    mock_user_repository.get_by_email.return_value = None

    with pytest.raises(BusinessRuleException) as excinfo:
        update_user_type_rule.execute(email, user_type)

    assert "User type update failed. Provided email is invalid." in str(excinfo.value)
    mock_user_repository.get_by_email.assert_called_once_with(email)
    mock_event_publisher.publish.assert_not_called()
