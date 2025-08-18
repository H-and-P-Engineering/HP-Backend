from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.business_verification.domain.enums import VerificationStatus
from apps.business_verification.infrastructure.models import (
    BusinessProfile,
    BusinessVerification,
)
from apps.users.infrastructure.models import User


@pytest.mark.django_db
class TestBusinessProfileModel:
    def test_create_business_profile(self):
        user = User.objects.create_user(email="test@example.com", password="testpass")

        profile = BusinessProfile.objects.create(
            user=user,
            business_name="Test Business",
            registration_number="RC123456",
            business_email="test@business.com",
            address="123 Business St",
            phone_number="+234123456789",
            website="https://testbusiness.com",
        )

        assert profile.id is not None
        assert profile.uuid is not None
        assert profile.user == user
        assert profile.business_name == "Test Business"
        assert profile.registration_number == "RC123456"
        assert profile.business_email == "test@business.com"
        assert profile.address == "123 Business St"
        assert profile.phone_number == "+234123456789"
        assert profile.website == "https://testbusiness.com"
        assert profile.is_business_email_verified is False
        assert profile.verification is None
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_business_profile_str_representation(self):
        user = User.objects.create_user(email="test@example.com", password="testpass")
        profile = BusinessProfile.objects.create(
            user=user,
            business_name="Test Business",
            registration_number="RC123456",
            business_email="test@business.com",
        )

        assert str(profile) == "Test Business (RC123456)"

    def test_business_profile_unique_registration_number(self):
        user1 = User.objects.create_user(email="test1@example.com", password="testpass")
        user2 = User.objects.create_user(email="test2@example.com", password="testpass")

        BusinessProfile.objects.create(
            user=user1,
            business_name="Business 1",
            registration_number="RC123456",
            business_email="test1@business.com",
        )

        with pytest.raises(IntegrityError):
            BusinessProfile.objects.create(
                user=user2,
                business_name="Business 2",
                registration_number="RC123456",  # Duplicate
                business_email="test2@business.com",
            )

    def test_business_profile_unique_email(self):
        user1 = User.objects.create_user(email="test1@example.com", password="testpass")
        user2 = User.objects.create_user(email="test2@example.com", password="testpass")

        BusinessProfile.objects.create(
            user=user1,
            business_name="Business 1",
            registration_number="RC123456",
            business_email="test@business.com",
        )

        with pytest.raises(IntegrityError):
            BusinessProfile.objects.create(
                user=user2,
                business_name="Business 2",
                registration_number="RC654321",
                business_email="test@business.com",  # Duplicate
            )


@pytest.mark.django_db
class TestBusinessVerificationModel:
    def test_create_business_verification(self):
        user = User.objects.create_user(email="test@example.com", password="testpass")

        verification = BusinessVerification.objects.create(
            user=user,
            business_registration_number="RC123456",
            business_name="Test Business",
            business_email="test@business.com",
            country_code="NG",
            verification_provider="youverify",
            verification_provider_reference="REF123456",
        )

        assert verification.id is not None
        assert verification.uuid is not None
        assert verification.user == user
        assert verification.business_registration_number == "RC123456"
        assert verification.business_name == "Test Business"
        assert verification.business_email == "test@business.com"
        assert verification.country_code == "NG"
        assert verification.verification_provider == "youverify"
        assert verification.verification_provider_reference == "REF123456"
        assert verification.verification_status == VerificationStatus.PENDING
        assert verification.created_at is not None
        assert verification.updated_at is not None

    def test_business_verification_str_representation(self):
        user = User.objects.create_user(email="test@example.com", password="testpass")
        verification = BusinessVerification.objects.create(
            user=user,
            business_registration_number="RC123456",
            business_name="Test Business",
            business_email="test@business.com",
        )

        assert str(verification) == "Verification for Test Business (RC123456)"

    def test_business_verification_status_choices(self):
        for status in VerificationStatus.values():
            user = User.objects.create_user(
                email=f"test{status}@example.com", password="testpass"
            )
            verification = BusinessVerification.objects.create(
                user_id=user.id,
                business_registration_number=f"RC{status}",
                business_name=f"Business {status}",
                business_email=f"{status.lower()}@business.com",
                verification_status=status,
            )
            assert verification.verification_status == status
