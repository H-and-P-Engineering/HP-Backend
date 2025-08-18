import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.users.infrastructure.models import User


@pytest.mark.django_db
class TestUserModelEdgeCases:
    def test_create_user_empty_phone_number_allowed(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass", phone_number=""
        )
        assert user.phone_number == ""

    def test_create_user_null_phone_number_allowed(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass", phone_number=None
        )
        assert user.phone_number is None

    def test_unique_phone_number_constraint_with_nulls(self):
        # Multiple users with null phone numbers should be allowed
        User.objects.create_user(
            email="test1@example.com", password="testpass", phone_number=None
        )

        User.objects.create_user(
            email="test2@example.com", password="testpass", phone_number=None
        )

    def test_unique_phone_number_constraint_with_empty_strings(self):
        # Multiple users with empty phone numbers should be allowed
        User.objects.create_user(
            email="test1@example.com", password="testpass", phone_number=""
        )

        User.objects.create_user(
            email="test2@example.com", password="testpass", phone_number=""
        )

    def test_user_str_representation(self):
        user = User.objects.create_user(email="test@example.com", password="testpass")
        assert str(user) == "test@example.com"

    def test_user_str_representation_with_special_characters(self):
        email = "test+special@example-domain.co.uk"
        user = User.objects.create_user(email=email, password="testpass")
        assert str(user) == email

    def test_username_field_is_email(self):
        assert User.USERNAME_FIELD == "email"

    def test_required_fields_empty(self):
        assert User.REQUIRED_FIELDS == []

    def test_user_type_choices_validation(self):
        from apps.users.domain.enums import UserType

        # Valid user type
        user = User.objects.create_user(
            email="test@example.com", password="testpass", user_type=UserType.VENDOR
        )
        assert user.user_type == UserType.VENDOR

    def test_default_values(self):
        user = User.objects.create_user(email="test@example.com", password="testpass")

        assert user.is_email_verified is False
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.user_type == "CLIENT"  # Default value
        assert user.uuid is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_auto_fields_not_editable(self):
        user = User.objects.create_user(email="test@example.com", password="testpass")

        original_uuid = user.uuid
        original_created_at = user.created_at

        # Update user
        user.first_name = "Updated"
        user.save()

        user.refresh_from_db()

        # UUID and created_at should not change
        assert user.uuid == original_uuid
        assert user.created_at == original_created_at
        assert user.first_name == "Updated"
