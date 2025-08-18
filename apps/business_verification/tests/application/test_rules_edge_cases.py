from unittest.mock import Mock

import pytest

from apps.business_verification.application.rules import CreateBusinessProfileRule
from apps.business_verification.domain.models import BusinessProfile
from apps.users.domain.enums import UserType
from apps.users.domain.models import User as DomainUser
from core.application.exceptions import BusinessRuleException


class TestCreateBusinessProfileRuleEdgeCases:
    def setup_method(self):
        self.mock_user_repository = Mock()
        self.mock_business_profile_repository = Mock()
        self.rule = CreateBusinessProfileRule(
            user_repository=self.mock_user_repository,
            business_profile_repository=self.mock_business_profile_repository,
        )

    def test_create_profile_valid_user_types(self):
        valid_types = [UserType.VENDOR, UserType.AGENT, UserType.SERVICE_PROVIDER]

        for user_type in valid_types:
            user = DomainUser(id=1, email="test@example.com", user_type=user_type)
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
                registration_number="RC123456",
            )

            assert result == profile

    def test_registration_number_processing_variations(self):
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

        test_cases = [
            "rc123456",  # lowercase
            "  RC123456  ",  # with spaces
            "Rc123456",  # mixed case
            "\tRC123456\n",  # with tabs and newlines
        ]

        for reg_number in test_cases:
            self.rule.execute(
                user_id=1,
                business_name="Test Business",
                business_email="test@business.com",
                registration_number=reg_number,
            )

            # Check that the created profile has normalized registration number
            call_args = self.mock_business_profile_repository.create.call_args[0][0]
            assert call_args.registration_number == "RC123456"

    def test_create_profile_with_all_optional_fields_none(self):
        user = DomainUser(id=1, email="test@example.com", user_type=UserType.VENDOR)
        profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
            address=None,
            phone_number=None,
            website=None,
        )

        self.mock_user_repository.get_by_id.return_value = user
        self.mock_business_profile_repository.get_by_user_id.return_value = None
        self.mock_business_profile_repository.create.return_value = profile

        result = self.rule.execute(
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
            address=None,
            phone_number=None,
            website=None,
        )

        call_args = self.mock_business_profile_repository.create.call_args[0][0]
        assert call_args.address is None
        assert call_args.phone_number is None
        assert call_args.website is None

    def test_create_profile_with_empty_string_optional_fields(self):
        user = DomainUser(id=1, email="test@example.com", user_type=UserType.VENDOR)
        profile = BusinessProfile(
            id=1,
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
            address="",
            phone_number="",
            website="",
        )

        self.mock_user_repository.get_by_id.return_value = user
        self.mock_business_profile_repository.get_by_user_id.return_value = None
        self.mock_business_profile_repository.create.return_value = profile

        result = self.rule.execute(
            user_id=1,
            business_name="Test Business",
            business_email="test@business.com",
            registration_number="RC123456",
            address="",
            phone_number="",
            website="",
        )

        call_args = self.mock_business_profile_repository.create.call_args[0][0]
        assert call_args.address == ""
        assert call_args.phone_number == ""
        assert call_args.website == ""
