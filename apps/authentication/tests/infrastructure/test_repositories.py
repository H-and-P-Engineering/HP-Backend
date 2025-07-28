from datetime import UTC, datetime, timedelta

import pytest
from faker import Faker

from apps.authentication.domain.models import BlackListedToken as DomainBlackListedToken
from apps.authentication.infrastructure.models import (
    BlackListedToken as DjangoBlackListedToken,
)
from apps.authentication.infrastructure.repositories import (
    DjangoBlackListedTokenRepository,
)
from apps.users.infrastructure.models import User as DjangoORMUser


@pytest.fixture
def faker_instance():
    return Faker()


@pytest.fixture
def blacklisted_token_repository() -> DjangoBlackListedTokenRepository:
    return DjangoBlackListedTokenRepository()


@pytest.mark.django_db
def test_add_blacklisted_token(
    blacklisted_token_repository: DjangoBlackListedTokenRepository,
    faker_instance: Faker,
):
    user = DjangoORMUser.objects.create_user(
        email=faker_instance.email(), password=faker_instance.password()
    )
    access_token = faker_instance.uuid4()
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=30)

    domain_token = DomainBlackListedToken(
        access=access_token,
        user_id=user.id,
        expires_at=expires_at,
    )

    created_token = blacklisted_token_repository.add(domain_token)

    assert created_token.id is not None
    assert created_token.access == access_token
    assert created_token.user_id == user.id
    assert created_token.expires_at.replace(microsecond=0) == expires_at.replace(
        microsecond=0
    )
    assert created_token.created_at is not None

    from apps.authentication.infrastructure.models import (
        BlackListedToken as DjangoBlackListedTokenORM,
    )

    orm_token = DjangoBlackListedTokenORM.objects.get(access=access_token)
    assert orm_token.access == access_token
    assert orm_token.user.id == user.id


@pytest.mark.django_db
def test_exists_blacklisted_token_true(
    blacklisted_token_repository: DjangoBlackListedTokenRepository,
    faker_instance: Faker,
):
    user = DjangoORMUser.objects.create_user(
        email=faker_instance.email(), password="securepass"
    )
    access_token = faker_instance.uuid4()
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=30)

    DjangoBlackListedToken.objects.create(
        access=access_token,
        user=user,
        expires_at=expires_at,
    )

    assert blacklisted_token_repository.exists(access_token) is True


@pytest.mark.django_db
def test_exists_blacklisted_token_false(
    blacklisted_token_repository: DjangoBlackListedTokenRepository,
    faker_instance: Faker,
):
    assert blacklisted_token_repository.exists(faker_instance.uuid4()) is False
