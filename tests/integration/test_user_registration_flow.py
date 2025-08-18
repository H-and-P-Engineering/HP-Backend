from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from apps.authentication.application.rules import RegisterUserRule
from apps.authentication.infrastructure.services import DjangoPasswordServiceAdapter
from apps.users.infrastructure.repositories import DjangoUserRepository
from core.infrastructure.services import DjangoEventPublisherAdapter


@pytest.mark.django_db
class TestUserRegistrationIntegrationFlow(TestCase):
    def setUp(self):
        self.user_repository = DjangoUserRepository()
        self.password_service = DjangoPasswordServiceAdapter()

        # Mock event publisher to avoid actual event processing
        self.mock_event_publisher = Mock(spec=DjangoEventPublisherAdapter)

        self.rule = RegisterUserRule(
            user_repository=self.user_repository,
            password_service=self.password_service,
            event_publisher=self.mock_event_publisher,
        )

    def test_complete_user_registration_flow(self):
        # Test data
        email = "integration@example.com"
        password = "TestPass123!"
        first_name = "Integration"
        last_name = "Test"
        phone_number = "+234123456789"
        user_type = "VENDOR"

        # Execute registration
        created_user = self.rule.execute(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            user_type=user_type,
        )

        # Verify user was created correctly
        assert created_user.id is not None
        assert created_user.email == email
        assert created_user.first_name == first_name
        assert created_user.last_name == last_name
        assert created_user.phone_number == phone_number
        assert created_user.user_type == "VENDOR"
        assert created_user.is_new is True
        assert created_user.is_email_verified is False

        # Verify password was hashed
        assert created_user.password_hash is not None
        assert created_user.password_hash != password

        # Verify event was published
        self.mock_event_publisher.publish.assert_called_once()

        # Verify user exists in database
        from apps.users.infrastructure.models import User

        db_user = User.objects.get(email=email)
        assert db_user.email == email
        assert db_user.check_password(password)

    def test_registration_with_duplicate_email_raises_conflict(self):
        # Create first user
        email = "duplicate@example.com"
        self.rule.execute(
            email=email,
            password="TestPass123!",
            first_name="First",
            last_name="User",
            phone_number="+234123456789",
            user_type="CLIENT",
        )

        # Attempt to create second user with same email
        from core.infrastructure.exceptions import ConflictError

        with pytest.raises(ConflictError, match="email already exists"):
            self.rule.execute(
                email=email,  # Same email
                password="DifferentPass123!",
                first_name="Second",
                last_name="User",
                phone_number="+234987654321",
                user_type="VENDOR",
            )

    def test_registration_with_duplicate_phone_raises_conflict(self):
        # Create first user
        phone_number = "+234123456789"
        self.rule.execute(
            email="first@example.com",
            password="TestPass123!",
            first_name="First",
            last_name="User",
            phone_number=phone_number,
            user_type="CLIENT",
        )

        # Attempt to create second user with same phone
        from core.infrastructure.exceptions import ConflictError

        with pytest.raises(ConflictError, match="phone number already exists"):
            self.rule.execute(
                email="second@example.com",
                password="DifferentPass123!",
                first_name="Second",
                last_name="User",
                phone_number=phone_number,  # Same phone
                user_type="VENDOR",
            )
