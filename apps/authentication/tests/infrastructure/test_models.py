from datetime import UTC, datetime, timedelta

import pytest
from faker import Faker

from apps.authentication.infrastructure.models import BlackListedToken
from apps.users.infrastructure.models import User


@pytest.fixture
def faker_instance() -> Faker:
    return Faker()


@pytest.mark.django_db
def test_blacklisted_token_creation(faker_instance: Faker):
    user = User.objects.create_user(
        email=faker_instance.email(), password=faker_instance.password()
    )
    access_token = "unique_access_token"
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=30)

    token = BlackListedToken.objects.create(
        access=access_token,
        user=user,
        expires_at=expires_at,
    )

    assert token.id is not None
    assert token.access == access_token
    assert token.user == user
    assert token.expires_at.replace(microsecond=0) == expires_at.replace(microsecond=0)
    assert token.created_at is not None


@pytest.mark.django_db
def test_blacklisted_token_is_blacklisted_method(faker_instance: Faker):
    user = User.objects.create_user(
        email=faker_instance.email(), password=faker_instance.password()
    )
    access_token_1 = "token_to_blacklist_1"
    access_token_2 = "token_to_blacklist_2"
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=30)

    BlackListedToken.objects.create(
        access=access_token_1,
        user=user,
        expires_at=expires_at,
    )

    assert BlackListedToken.is_blacklisted(access_token_1) is True
    assert BlackListedToken.is_blacklisted(access_token_2) is False
    assert BlackListedToken.is_blacklisted("non_existent_token") is False


@pytest.mark.django_db
def test_blacklisted_token_access_uniqueness(faker_instance: Faker):
    user = User.objects.create_user(
        email=faker_instance.email(), password=faker_instance.password()
    )
    access_token = "duplicate_access_token"
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=30)

    BlackListedToken.objects.create(
        access=access_token,
        user=user,
        expires_at=expires_at,
    )

    with pytest.raises(Exception):
        BlackListedToken.objects.create(
            access=access_token,
            user=user,
            expires_at=expires_at,
        )
