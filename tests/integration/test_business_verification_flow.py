from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from apps.business_verification.application.rules import (
    CreateBusinessProfileRule,
    InitiateBusinessVerificationRule,
    ProcessBusinessVerificationRule,
)
from apps.business_verification.domain.enums import VerificationStatus
from apps.business_verification.domain.models import BusinessVerificationResult
from apps.business_verification.infrastructure.repositories import (
    DjangoBusinessProfileRepository,
    DjangoBusinessVerificationRepository,
)
from apps.business_verification.infrastructure.services import YouVerifyAdapter
from apps.users.infrastructure.models import User
from apps.users.infrastructure.repositories import DjangoUserRepository


@pytest.mark.django_db
class TestBusinessVerificationIntegrationFlow(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email="business@example.com", password="testpass", user_type="VENDOR"
        )

        # Initialize repositories
        self.user_repository = DjangoUserRepository()
        self.business_profile_repository = DjangoBusinessProfileRepository()
        self.business_verification_repository = DjangoBusinessVerificationRepository()

        # Mock services
        self.mock_verification_service = Mock(spec=YouVerifyAdapter)
        self.mock_event_publisher = Mock()

        # Initialize rules
        self.create_profile_rule = CreateBusinessProfileRule(
            user_repository=self.user_repository,
            business_profile_repository=self.business_profile_repository,
        )

        self.initiate_verification_rule = InitiateBusinessVerificationRule(
            business_profile_repository=self.business_profile_repository,
            business_verification_repository=self.business_verification_repository,
            verification_service=self.mock_verification_service,
            user_repository=self.user_repository,
            event_publisher=self.mock_event_publisher,
        )

        self.process_verification_rule = ProcessBusinessVerificationRule(
            business_profile_repository=self.business_profile_repository,
            business_verification_repository=self.business_verification_repository,
            verification_service=self.mock_verification_service,
            event_publisher=self.mock_event_publisher,
        )

    def test_complete_business_verification_success_flow(self):
        # Step 1: Create business profile
        profile = self.create_profile_rule.execute(
            user_id=self.user.id,
            business_name="Test Business Ltd",
            business_email="test@business.com",
            registration_number="RC123456",
            address="123 Business Street",
            phone_number="+234123456789",
            website="https://testbusiness.com",
        )

        assert profile.id is not None
        assert profile.business_name == "Test Business Ltd"
        assert profile.registration_number == "RC123456"

        # Step 2: Initiate verification
        verification = self.initiate_verification_rule.execute(
            user_id=self.user.id, country_code="NG"
        )

        assert verification.id is not None
        assert verification.verification_status == VerificationStatus.PENDING
        assert verification.business_registration_number == "RC123456"

        # Verify event was published
        self.mock_event_publisher.publish.assert_called()

        # Step 3: Process verification (success scenario)
        self.mock_verification_service.verify_business.return_value = (
            BusinessVerificationResult(
                success=True,
                provider_reference="REF123456",
                business_data={"status": "active", "company_name": "Test Business Ltd"},
            )
        )

        self.process_verification_rule.execute(verification.id)

        # Verify verification was updated
        updated_verification = self.business_verification_repository.get_by_id(
            verification.id
        )
        assert updated_verification.verification_status == VerificationStatus.SUCCESSFUL

        # Verify events were published (success and email events)
        assert self.mock_event_publisher.publish.call_count >= 2

    def test_complete_business_verification_failure_flow(self):
        # Step 1: Create business profile
        profile = self.create_profile_rule.execute(
            user_id=self.user.id,
            business_name="Invalid Business",
            business_email="invalid@business.com",
            registration_number="RC999999",
        )

        # Step 2: Initiate verification
        verification = self.initiate_verification_rule.execute(
            user_id=self.user.id, country_code="NG"
        )

        # Step 3: Process verification (failure scenario)
        self.mock_verification_service.verify_business.return_value = (
            BusinessVerificationResult(
                success=False, error_message="Business not found in registry"
            )
        )

        self.process_verification_rule.execute(verification.id)

        # Verify verification was marked as failed
        updated_verification = self.business_verification_repository.get_by_id(
            verification.id
        )
        assert updated_verification.verification_status == VerificationStatus.FAILED

        # Verify failure event was published
        self.mock_event_publisher.publish.assert_called()

    def test_verification_with_existing_profile_retry(self):
        # Create initial profile and verification
        profile = self.create_profile_rule.execute(
            user_id=self.user.id,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
        )

        first_verification = self.initiate_verification_rule.execute(
            user_id=self.user.id, country_code="NG"
        )

        # Simulate failed verification
        self.mock_verification_service.verify_business.return_value = (
            BusinessVerificationResult(
                success=False, error_message="Temporary service unavailable"
            )
        )

        self.process_verification_rule.execute(first_verification.id)

        # Reset mock
        self.mock_event_publisher.reset_mock()

        # Retry verification
        retry_verification = self.initiate_verification_rule.execute(
            user_id=self.user.id, country_code="NG"
        )

        # Should return the same verification object with reset status
        assert retry_verification.id == first_verification.id
        assert retry_verification.verification_status == VerificationStatus.PENDING

        # Verify retry event was published
        self.mock_event_publisher.publish.assert_called()
