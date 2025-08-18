from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from apps.business_verification.application.rules import (
    CreateBusinessProfileRule,
    InitiateBusinessVerificationRule,
    ProcessBusinessVerificationRule,
    VerifyBusinessEmailRule,
)
from apps.business_verification.domain.enums import VerificationStatus
from apps.business_verification.domain.models import (
    BusinessProfile,
    BusinessVerification,
    BusinessVerificationResult,
)
from apps.users.domain.enums import UserType
from apps.users.domain.models import User as DomainUser
from core.application.exceptions import BusinessRuleException


class TestCreateBusinessProfileRule:
    def setup_method(self):
        self.mock_user_repository = Mock()
        self.mock_business_profile_repository = Mock()
        self.rule = CreateBusinessProfileRule(
            user_repository=self.mock_user_repository,
            business_profile_repository=self.mock_business_profile_repository,
        )

    def test_create_business_profile_success(self):
        user = DomainUser(id=1, email="test@example.com", user_type=UserType.VENDOR)
        profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
        )

        self.mock_user_repository.get_by_id.return_value = user
        self.mock_business_profile_repository.get_by_user_id.return_value = None
        self.mock_business_profile_repository.create.return_value = profile

        result = self.rule.execute(
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="rc123456",  # Should be uppercased and stripped
            address="123 Business St",
            phone_number="+234123456789",
            website="https://testbusiness.com",
        )

        self.mock_user_repository.get_by_id.assert_called_once_with(1)
        self.mock_business_profile_repository.get_by_user_id.assert_called_once_with(1)
        self.mock_business_profile_repository.create.assert_called_once()

        # Check that registration number was processed correctly
        call_args = self.mock_business_profile_repository.create.call_args[0][0]
        assert call_args.registration_number == "RC123456"
        assert result == profile

    def test_create_business_profile_user_not_found(self):
        self.mock_user_repository.get_by_id.return_value = None

        with pytest.raises(BusinessRuleException, match="User not found"):
            self.rule.execute(
                user_id=1,
                business_name="Test Business",
                business_email="test@business.com",
                registration_number="RC123456",
            )

    def test_create_business_profile_invalid_user_type_client(self):
        user = DomainUser(id=1, email="test@example.com", user_type=UserType.CLIENT)
        self.mock_user_repository.get_by_id.return_value = user

        with pytest.raises(
            BusinessRuleException, match="User does not need business profile"
        ):
            self.rule.execute(
                user_id=1,
                business_name="Test Business",
                business_email="test@business.com",
                registration_number="RC123456",
            )

    def test_create_business_profile_invalid_user_type_admin(self):
        user = DomainUser(id=1, email="test@example.com", user_type=UserType.ADMIN)
        self.mock_user_repository.get_by_id.return_value = user

        with pytest.raises(
            BusinessRuleException, match="User does not need business profile"
        ):
            self.rule.execute(
                user_id=1,
                business_name="Test Business",
                business_email="test@business.com",
                registration_number="RC123456",
            )

    def test_create_business_profile_already_exists(self):
        user = DomainUser(id=1, email="test@example.com", user_type=UserType.VENDOR)
        existing_profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Existing Business",
            business_email="existing@business.com",
            registration_number="RC999999",
        )

        self.mock_user_repository.get_by_id.return_value = user
        self.mock_business_profile_repository.get_by_user_id.return_value = (
            existing_profile
        )

        with pytest.raises(
            BusinessRuleException, match="Business profile already exists"
        ):
            self.rule.execute(
                user_id=1,
                business_name="Test Business",
                business_email="test@business.com",
                registration_number="RC123456",
            )


class TestInitiateBusinessVerificationRule:
    def setup_method(self):
        self.mock_business_profile_repository = Mock()
        self.mock_business_verification_repository = Mock()
        self.mock_verification_service = Mock()
        self.mock_user_repository = Mock()
        self.mock_event_publisher = Mock()

        self.rule = InitiateBusinessVerificationRule(
            business_profile_repository=self.mock_business_profile_repository,
            business_verification_repository=self.mock_business_verification_repository,
            verification_service=self.mock_verification_service,
            user_repository=self.mock_user_repository,
            event_publisher=self.mock_event_publisher,
        )

    def test_initiate_verification_new_verification(self):
        profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
        )
        verification = BusinessVerification(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
            country_code="NG",
        )

        self.mock_business_profile_repository.get_by_user_id.return_value = profile
        self.mock_business_verification_repository.get_by_user_id.return_value = None
        self.mock_business_verification_repository.create.return_value = verification

        result = self.rule.execute(user_id=1, country_code="NG")

        self.mock_business_profile_repository.get_by_user_id.assert_called_once_with(1)
        self.mock_business_verification_repository.get_by_user_id.assert_called_once_with(
            1
        )
        self.mock_business_verification_repository.create.assert_called_once()
        self.mock_event_publisher.publish.assert_called_once()

        assert result == verification

    def test_initiate_verification_existing_pending_verification(self):
        profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
        )
        existing_verification = BusinessVerification(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
            verification_status=VerificationStatus.FAILED,
        )

        self.mock_business_profile_repository.get_by_user_id.return_value = profile
        self.mock_business_verification_repository.get_by_user_id.return_value = (
            existing_verification
        )

        result = self.rule.execute(user_id=1)

        self.mock_event_publisher.publish.assert_called_once()
        assert result.verification_status == VerificationStatus.PENDING

    def test_initiate_verification_already_successful(self):
        profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
        )
        existing_verification = BusinessVerification(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
            verification_status=VerificationStatus.SUCCESSFUL,
        )

        self.mock_business_profile_repository.get_by_user_id.return_value = profile
        self.mock_business_verification_repository.get_by_user_id.return_value = (
            existing_verification
        )

        with pytest.raises(
            BusinessRuleException, match="Business verification already successful"
        ):
            self.rule.execute(user_id=1)

    def test_initiate_verification_no_profile(self):
        self.mock_business_profile_repository.get_by_user_id.return_value = None

        with pytest.raises(BusinessRuleException, match="Business profile not found"):
            self.rule.execute(user_id=1)


class TestProcessBusinessVerificationRule:
    def setup_method(self):
        self.mock_business_profile_repository = Mock()
        self.mock_business_verification_repository = Mock()
        self.mock_verification_service = Mock()
        self.mock_event_publisher = Mock()

        self.rule = ProcessBusinessVerificationRule(
            business_profile_repository=self.mock_business_profile_repository,
            business_verification_repository=self.mock_business_verification_repository,
            verification_service=self.mock_verification_service,
            event_publisher=self.mock_event_publisher,
        )

    def test_process_verification_success(self):
        verification = BusinessVerification(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
            country_code="NG",
        )
        result = BusinessVerificationResult(
            success=True,
            provider_reference="REF123456",
            business_data={"status": "active"},
        )

        self.mock_business_verification_repository.get_by_id.return_value = verification
        self.mock_verification_service.verify_business.return_value = result

        self.rule.execute(verification_id=1)

        # Should update status to IN_PROGRESS first
        update_calls = self.mock_business_verification_repository.update.call_args_list
        assert len(update_calls) == 2
        assert (
            update_calls[0][1]["verification_status"] == VerificationStatus.IN_PROGRESS
        )
        assert (
            update_calls[1][1]["verification_status"] == VerificationStatus.SUCCESSFUL
        )

        # Should publish success events
        publish_calls = self.mock_event_publisher.publish.call_args_list
        assert len(publish_calls) == 2

    def test_process_verification_failure(self):
        verification = BusinessVerification(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
            country_code="NG",
        )
        result = BusinessVerificationResult(
            success=False, error_message="Business not found"
        )

        self.mock_business_verification_repository.get_by_id.return_value = verification
        self.mock_verification_service.verify_business.return_value = result

        self.rule.execute(verification_id=1)

        # Should update status to FAILED
        update_calls = self.mock_business_verification_repository.update.call_args_list
        assert len(update_calls) == 2
        assert update_calls[1][1]["verification_status"] == VerificationStatus.FAILED

        # Should publish failure event
        self.mock_event_publisher.publish.assert_called()

    def test_process_verification_exception(self):
        verification = BusinessVerification(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
            country_code="NG",
        )

        self.mock_business_verification_repository.get_by_id.return_value = verification
        self.mock_verification_service.verify_business.side_effect = Exception(
            "API Error"
        )

        self.rule.execute(verification_id=1)

        # Should update status to FAILED and publish failure event
        update_calls = self.mock_business_verification_repository.update.call_args_list
        assert len(update_calls) == 2
        assert update_calls[1][1]["verification_status"] == VerificationStatus.FAILED

        self.mock_event_publisher.publish.assert_called()

    def test_process_verification_not_found(self):
        self.mock_business_verification_repository.get_by_id.return_value = None

        # Should return without error
        self.rule.execute(verification_id=999)

        self.mock_verification_service.verify_business.assert_not_called()
        self.mock_event_publisher.publish.assert_not_called()


class TestVerifyBusinessEmailRule:
    def setup_method(self):
        self.mock_cache_service = Mock()
        self.mock_business_profile_repository = Mock()
        self.mock_business_verification_repository = Mock()
        self.mock_event_publisher = Mock()

        self.rule = VerifyBusinessEmailRule(
            cache_service=self.mock_cache_service,
            business_profile_repository=self.mock_business_profile_repository,
            business_verification_repository=self.mock_business_verification_repository,
            event_publisher=self.mock_event_publisher,
        )

    def test_verify_business_email_success(self):
        verification_uuid = "123e4567-e89b-12d3-a456-426614174000"
        token = "test_token"
        cached_data = (1, token)

        business_profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
            is_business_email_verified=False,
        )
        verification = BusinessVerification(
            id=1,
            uuid=verification_uuid,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
        )

        self.mock_cache_service.get.return_value = cached_data
        self.mock_business_profile_repository.get_by_verification_id.return_value = (
            business_profile
        )
        self.mock_business_verification_repository.get_by_id.return_value = verification

        self.rule.execute(verification_uuid, token)

        self.mock_cache_service.get.assert_called_once_with(
            f"email_verify_{verification_uuid}"
        )
        self.mock_business_profile_repository.get_by_verification_id.assert_called_once_with(
            1
        )
        self.mock_business_verification_repository.get_by_id.assert_called_once_with(1)
        self.mock_event_publisher.publish.assert_called_once()

    def test_verify_business_email_invalid_session(self):
        verification_uuid = "123e4567-e89b-12d3-a456-426614174000"
        token = "test_token"

        self.mock_cache_service.get.return_value = None

        with pytest.raises(
            BusinessRuleException, match="Verification session is invalid or expired"
        ):
            self.rule.execute(verification_uuid, token)

    def test_verify_business_email_already_verified(self):
        verification_uuid = "123e4567-e89b-12d3-a456-426614174000"
        token = "test_token"
        cached_data = (1, token)

        business_profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
            is_business_email_verified=True,
        )

        self.mock_cache_service.get.return_value = cached_data
        self.mock_business_profile_repository.get_by_verification_id.return_value = (
            business_profile
        )

        with pytest.raises(
            BusinessRuleException, match="Business email is already verified"
        ):
            self.rule.execute(verification_uuid, token)

    def test_verify_business_email_invalid_token(self):
        verification_uuid = "123e4567-e89b-12d3-a456-426614174000"
        token = "wrong_token"
        cached_data = (1, "correct_token")

        business_profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
            is_business_email_verified=False,
        )
        verification = BusinessVerification(
            id=1,
            uuid=verification_uuid,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
        )

        self.mock_cache_service.get.return_value = cached_data
        self.mock_business_profile_repository.get_by_verification_id.return_value = (
            business_profile
        )
        self.mock_business_verification_repository.get_by_id.return_value = verification

        with pytest.raises(
            BusinessRuleException,
            match="Provided verification id or verification token is invalid",
        ):
            self.rule.execute(verification_uuid, token)
