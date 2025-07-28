from datetime import datetime
from uuid import uuid4

from apps.users.domain.enums import UserType
from apps.users.domain.models import User


def test_user_creation_with_minimal_data():
    email = "test@example.com"
    user = User(email=email)

    assert user.email == email
    assert user.password_hash is None
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.user_type == UserType.CLIENT
    assert user.is_email_verified is False
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_new is True
    assert user.id is None
    assert user.uuid is None
    assert user.created_at is None
    assert user.updated_at is None
    assert user.last_login is None


def test_user_creation_with_all_data():
    user_id = 1
    user_uuid = uuid4()
    email = "full_test@example.com"
    password = "hashed_password"
    first_name = "John"
    last_name = "Doe"
    user_type = UserType.ADMIN
    is_email_verified = True
    is_active = False
    is_staff = True
    is_superuser = True
    is_new = True
    created_at = datetime.now()
    updated_at = datetime.now()
    last_login = datetime.now()

    user = User(
        id=user_id,
        uuid=user_uuid,
        email=email,
        password_hash=password,
        first_name=first_name,
        last_name=last_name,
        user_type=user_type,
        is_email_verified=is_email_verified,
        is_active=is_active,
        is_staff=is_staff,
        is_superuser=is_superuser,
        is_new=is_new,
        created_at=created_at,
        updated_at=updated_at,
        last_login=last_login,
    )

    assert user.id == user_id
    assert user.uuid == user_uuid
    assert user.email == email
    assert user.password_hash == password
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert user.user_type == user_type
    assert user.is_email_verified == is_email_verified
    assert user.is_active == is_active
    assert user.is_staff == is_staff
    assert user.is_superuser == is_superuser
    assert user.is_new == is_new
    assert user.created_at == created_at
    assert user.updated_at == updated_at
    assert user.last_login == last_login
