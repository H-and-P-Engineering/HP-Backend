from datetime import datetime
from uuid import uuid4

import pytest

from apps.business_verification.domain.enums import VerificationStatus
from apps.business_verification.domain.models import (
    BusinessProfile,
    BusinessVerification,
    BusinessVerificationResult,
)


class TestBusinessProfile:
    def test_business_profile_creation_minimal_data(self):
        profile = BusinessProfile(
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
        )

        assert profile.user_id == 1
        assert profile.business_name == "Test Business"
        assert profile.business_email == "test@business.com"
        assert profile.registration_number == "RC123456"
        assert profile.address is None
        assert profile.phone_number is None
        assert profile.website is None
        assert profile.verification_id is None
        assert profile.is_business_email_verified is False
        assert profile.id is None
        assert profile.uuid is None
        assert profile.created_at is None
        assert profile.updated_at is None

    def test_business_profile_creation_full_data(self):
        profile_id = 1
        profile_uuid = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()

        profile = BusinessProfile(
            id=profile_id,
            uuid=profile_uuid,
            user_id=1,
            business_name="Test Business Ltd",
            business_email="contact@testbusiness.com",
            registration_number="RC123456",
            address="123 Business Street",
            phone_number="+234123456789",
            website="https://testbusiness.com",
            verification_id=1,
            is_business_email_verified=True,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert profile.id == profile_id
        assert profile.uuid == profile_uuid
        assert profile.user_id == 1
        assert profile.business_name == "Test Business Ltd"
        assert profile.business_email == "contact@testbusiness.com"
        assert profile.registration_number == "RC123456"
        assert profile.address == "123 Business Street"
        assert profile.phone_number == "+234123456789"
        assert profile.website == "https://testbusiness.com"
        assert profile.verification_id == 1
        assert profile.is_business_email_verified is True
        assert profile.created_at == created_at
        assert profile.updated_at == updated_at


class TestBusinessVerification:
    def test_business_verification_creation_minimal_data(self):
        verification = BusinessVerification(
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            business_registration_number="RC123456",
        )

        assert verification.user_id == 1
        assert verification.business_name == "Test Business"
        assert verification.business_email == "test@business.com"
        assert verification.business_registration_number == "RC123456"
        assert verification.country_code == "NG"
        assert verification.verification_provider is None
        assert verification.verification_provider_reference is None
        assert verification.verification_status == VerificationStatus.PENDING
        assert verification.id is None
        assert verification.uuid is None
        assert verification.created_at is None
        assert verification.updated_at is None

    def test_business_verification_creation_full_data(self):
        verification_id = 1
        verification_uuid = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()

        verification = BusinessVerification(
            id=verification_id,
            uuid=verification_uuid,
            user_id=1,
            business_name="Test Business Ltd",
            business_email="contact@testbusiness.com",
            business_registration_number="RC123456",
            country_code="US",
            verification_provider="youverify",
            verification_provider_reference="REF123456",
            verification_status=VerificationStatus.SUCCESSFUL,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert verification.id == verification_id
        assert verification.uuid == verification_uuid
        assert verification.user_id == 1
        assert verification.business_name == "Test Business Ltd"
        assert verification.business_email == "contact@testbusiness.com"
        assert verification.business_registration_number == "RC123456"
        assert verification.country_code == "US"
        assert verification.verification_provider == "youverify"
        assert verification.verification_provider_reference == "REF123456"
        assert verification.verification_status == VerificationStatus.SUCCESSFUL
        assert verification.created_at == created_at
        assert verification.updated_at == updated_at


class TestBusinessVerificationResult:
    def test_business_verification_result_success(self):
        business_data = {"company_name": "Test Business", "status": "active"}

        result = BusinessVerificationResult(
            success=True, provider_reference="REF123456", business_data=business_data
        )

        assert result.success is True
        assert result.provider_reference == "REF123456"
        assert result.business_data == business_data
        assert result.error_message is None

    def test_business_verification_result_failure(self):
        result = BusinessVerificationResult(
            success=False, error_message="Business not found"
        )

        assert result.success is False
        assert result.provider_reference is None
        assert result.business_data is None
        assert result.error_message == "Business not found"
