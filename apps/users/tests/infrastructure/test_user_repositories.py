from datetime import UTC, datetime

import pytest
from faker import Faker

from apps.users.domain.enums import UserType
from apps.users.domain.models import User as DomainUser
from apps.users.infrastructure.models import User as DjangoORMUser
from apps.users.infrastructure.repositories import DjangoUserRepository


@pytest.fixture(scope="module")
def faker_instance() -> Faker:
    return Faker()


@pytest.fixture(scope="module")
def user_repository() -> DjangoUserRepository:
    return DjangoUserRepository()


@pytest.mark.django_db
def test_create_user(user_repository: DjangoUserRepository, faker_instance: Faker):
    email = faker_instance.email()
    hashed_password = faker_instance.password()
    domain_user = DomainUser(email=email, password_hash=hashed_password)

    created_user = user_repository.create(domain_user)

    assert created_user.id is not None
    assert created_user.uuid is not None
    assert created_user.email == email
    assert created_user.password_hash is not None
    assert created_user.is_active is True

    django_user = DjangoORMUser.objects.get(email=email)

    assert django_user.email == email
    assert django_user.password == hashed_password
    assert django_user.is_active is True


@pytest.mark.django_db
def test_create_multiple_users(
    user_repository: DjangoUserRepository, faker_instance: Faker
):
    created_users = []

    for i in range(20):
        created_users.append(
            user_repository.create(
                DomainUser(
                    email=faker_instance.email(), password_hash=faker_instance.password
                )
            )
        )

    index = 1

    for user in created_users:
        if user != created_users[-1]:
            while True:
                next_user = created_users[created_users.index(user) + index]
                assert (user.uuid, user.email, user.id) != (
                    next_user.uuid,
                    next_user.email,
                    next_user.id,
                )
                if (
                    created_users[created_users.index(user) + index]
                    == created_users[-1]
                ):
                    break
                index += 1
        index = 1


@pytest.mark.django_db
def test_create_social_user(
    user_repository: DjangoUserRepository, faker_instance: Faker
):
    email = faker_instance.email()
    domain_user = DomainUser(email=email, first_name=faker_instance.first_name())

    created_django_user = user_repository.create(domain_user, is_social=True)

    assert created_django_user.id is not None
    assert created_django_user.email == email
    assert created_django_user.first_name == domain_user.first_name

    assert DjangoORMUser.objects.filter(email=email).exists()


@pytest.mark.django_db
def test_get_user_by_email(
    user_repository: DjangoUserRepository, faker_instance: Faker
):
    email = faker_instance.email()
    password = faker_instance.password()
    django_user = DjangoORMUser.objects.create_user(email=email, password=password)

    retrieved_user = user_repository.get_by_email(email)

    assert retrieved_user is not None
    assert retrieved_user.email == email
    assert retrieved_user.id == django_user.id


@pytest.mark.django_db
def test_get_non_existent_user_by_email(
    user_repository: DjangoUserRepository, faker_instance: Faker
):
    email = faker_instance.email()
    retrieved_user = user_repository.get_by_email(email)
    assert retrieved_user is None


@pytest.mark.django_db
def test_get_user_by_id(user_repository: DjangoUserRepository, faker_instance: Faker):
    email = faker_instance.email()
    password = faker_instance.password()
    django_user = DjangoORMUser.objects.create_user(email=email, password=password)

    retrieved_user = user_repository.get_by_id(django_user.id)

    assert retrieved_user is not None
    assert retrieved_user.email == email
    assert retrieved_user.id == django_user.id


@pytest.mark.django_db
def test_get_non_existent_user_by_id(
    user_repository: DjangoUserRepository, faker_instance: Faker
):
    retrieved_user = user_repository.get_by_id(99999)
    assert retrieved_user is None


@pytest.mark.django_db
def test_update_user(user_repository: DjangoUserRepository, faker_instance: Faker):
    email = faker_instance.email()
    password = faker_instance.password()
    original_first_name = faker_instance.first_name()
    django_user = DjangoORMUser.objects.create_user(
        email=email, password=password, first_name=original_first_name
    )

    updated_first_name = faker_instance.first_name()
    updated_last_name = faker_instance.last_name()

    domain_user_to_update = DomainUser(
        id=django_user.id,
        email=django_user.email,
        password_hash=django_user.password,
        first_name=updated_first_name,
        last_name=updated_last_name,
        user_type=UserType.AGENT,
        is_active=False,
    )

    updated_domain_user = user_repository.update(
        domain_user_to_update, return_raw=False
    )

    assert updated_domain_user.id == domain_user_to_update.id
    assert updated_domain_user.first_name == updated_first_name
    assert updated_domain_user.last_name == updated_last_name
    assert updated_domain_user.user_type == UserType.AGENT
    assert updated_domain_user.is_active is False

    refreshed_django_user = DjangoORMUser.objects.get(id=django_user.id)

    assert refreshed_django_user.first_name == updated_first_name
    assert refreshed_django_user.last_name == updated_last_name
    assert refreshed_django_user.user_type == UserType.AGENT.value
    assert refreshed_django_user.is_active is False


@pytest.mark.django_db
def test_update_user_with_kwargs(
    user_repository: DjangoUserRepository, faker_instance: Faker
):
    email = faker_instance.email()
    password = faker_instance.password()
    django_user = DjangoORMUser.objects.create_user(email=email, password=password)

    domain_user_for_lookup = DomainUser(id=django_user.id, email=django_user.email)

    new_first_name = faker_instance.first_name()
    updated_django_user = user_repository.update(
        domain_user_for_lookup, first_name=new_first_name
    )

    assert updated_django_user.first_name == new_first_name

    refreshed_django_user = DjangoORMUser.objects.get(id=django_user.id)

    assert refreshed_django_user.first_name == new_first_name


@pytest.mark.django_db
def test_update_user_with_unacceptable_fields(
    user_repository: DjangoUserRepository, faker_instance: Faker
):
    email = faker_instance.email()
    password = faker_instance.password()
    original_first_name = faker_instance.first_name()
    django_user = DjangoORMUser.objects.create_user(
        email=email, password=password, first_name=original_first_name
    )

    updated_uuid = faker_instance.uuid4()
    updated_password = faker_instance.password()
    updated_created_at = datetime.now(tz=UTC)
    updated_last_login = datetime.now(tz=UTC)

    domain_user_to_update = DomainUser(
        id=django_user.id,
        email=django_user.email,
        password_hash=updated_password,
        uuid=updated_uuid,
    )

    updated_domain_user = user_repository.update(
        domain_user_to_update,
        return_raw=False,
        user_type="ADMIN",
        password=updated_password,
        last_login=updated_last_login,
        created_at=updated_created_at,
    )

    assert updated_domain_user.password_hash != updated_password
    assert updated_domain_user.uuid != updated_uuid
    assert updated_domain_user.user_type != UserType.ADMIN
    assert updated_domain_user.created_at != updated_created_at
    assert updated_domain_user.last_login == updated_last_login
