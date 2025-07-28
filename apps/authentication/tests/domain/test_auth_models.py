from datetime import datetime, timedelta

from apps.authentication.domain.models import BlackListedToken


def test_blacklisted_token_creation_minimal_data():
    access_token = "test_access_token"
    user_id = 123
    expires_at = datetime.now() + timedelta(minutes=30)

    blacklisted_token = BlackListedToken(
        access=access_token, user_id=user_id, expires_at=expires_at
    )

    assert blacklisted_token.access == access_token
    assert blacklisted_token.user_id == user_id
    assert blacklisted_token.expires_at == expires_at
    assert blacklisted_token.id is None
    assert blacklisted_token.created_at is None


def test_blacklisted_token_creation_all_data():
    token_id = 1
    access_token = "another_access_token"
    user_id = 456
    expires_at = datetime.now() + timedelta(hours=1)
    created_at = datetime.now()

    blacklisted_token = BlackListedToken(
        id=token_id,
        access=access_token,
        user_id=user_id,
        expires_at=expires_at,
        created_at=created_at,
    )

    assert blacklisted_token.id == token_id
    assert blacklisted_token.access == access_token
    assert blacklisted_token.user_id == user_id
    assert blacklisted_token.expires_at == expires_at
    assert blacklisted_token.created_at == created_at
