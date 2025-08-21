from typing import Any, Dict

from django.conf import settings
from django.db import IntegrityError
from loguru import logger

from app.application.business_verification.ports import (
    IBusinessProfileRepository,
    IBusinessVerificationRepository,
)
from app.core.exceptions import BaseAPIException, ConflictError
from app.domain.business_verification.entities import (
    BusinessProfile as DomainBusinessProfile,
)
from app.domain.business_verification.entities import (
    BusinessVerification as DomainBusinessVerification,
)

from .models.tables import BusinessProfile, BusinessVerification


def from_domain_business_profile(profile: DomainBusinessProfile) -> Dict[str, Any]:
    return {
        "user_id": profile.user_id,
        "business_name": profile.business_name,
        "registration_number": profile.registration_number,
        "address": profile.address,
        "phone_number": profile.phone_number,
        "business_email": profile.business_email,
        "website": profile.website,
    }


def to_domain_business_profile(
    django_profile: BusinessProfile,
) -> DomainBusinessProfile:
    return DomainBusinessProfile(
        id=django_profile.id,
        uuid=django_profile.uuid,
        user_id=django_profile.user_id,
        business_name=django_profile.business_name,
        registration_number=django_profile.registration_number,
        address=django_profile.address,
        phone_number=django_profile.phone_number,
        business_email=django_profile.business_email,
        website=django_profile.website,
        verification_id=(
            django_profile.verification_id if django_profile.verification else None
        ),
        is_business_email_verified=django_profile.is_business_email_verified,
        created_at=django_profile.created_at,
        updated_at=django_profile.updated_at,
    )


def from_domain_business_verification(
    verification: DomainBusinessVerification,
) -> Dict[str, Any]:
    return {
        "user_id": verification.user_id,
        "business_registration_number": verification.business_registration_number,
        "business_name": verification.business_name,
        "country_code": verification.country_code,
        "verification_status": verification.verification_status,
        "verification_provider": verification.verification_provider,
        "verification_provider_reference": verification.verification_provider_reference,
        "business_email": verification.business_email,
    }


def to_domain_business_verification(
    django_verification: BusinessVerification,
) -> DomainBusinessVerification:
    return DomainBusinessVerification(
        id=django_verification.id,
        uuid=django_verification.uuid,
        user_id=django_verification.user_id,
        business_registration_number=django_verification.business_registration_number,
        business_name=django_verification.business_name,
        business_email=django_verification.business_email,
        country_code=django_verification.country_code,
        verification_status=django_verification.verification_status,
        verification_provider=django_verification.verification_provider,
        verification_provider_reference=django_verification.verification_provider_reference,
        created_at=django_verification.created_at,
        updated_at=django_verification.updated_at,
    )


class DjangoBusinessProfileRepository(IBusinessProfileRepository):
    def create(self, profile: DomainBusinessProfile) -> DomainBusinessProfile:
        try:
            django_profile = BusinessProfile.objects.create(
                **from_domain_business_profile(profile)
            )
            return to_domain_business_profile(django_profile)

        except IntegrityError as e:
            if "registration_number" in str(e):
                raise ConflictError(
                    "Business profile creation failed. Profile with provided registration number already exists."
                ) from e
            elif "business_email" in str(e):
                raise ConflictError(
                    "Business profile creation failed. Profile with business email already exists."
                ) from e

            logger.error(
                f"Integrity error during business profile creation for '{profile.business_email}': {e}"
            )
            raise ConflictError from e

        except Exception as e:
            logger.critical(
                f"Unhandled error during business profile creation for '{profile.business_email}': {e}"
            )
            raise BaseAPIException(
                "Business profile creation failed. Please try again later."
            )

    def update(self, profile: DomainBusinessProfile, **kwargs) -> DomainBusinessProfile:
        try:
            django_profile = BusinessProfile.objects.get(id=profile.id)

            for key, value in kwargs.items():
                if hasattr(django_profile, key) and key not in [
                    "user_id",
                    "uuid",
                    "id",
                    "created_at",
                ]:
                    setattr(django_profile, key, value)

            django_profile.save()
            return to_domain_business_profile(django_profile)

        except Exception as e:
            logger.critical(
                f"Unhandled error during business profile update for '{profile.business_name}': {e}"
            )
            raise BaseAPIException(
                "Business profile update failed. Please try again later."
            ) from e

    def get_by_user_id(self, user_id: int) -> DomainBusinessProfile | None:
        try:
            django_profile = BusinessProfile.objects.get(user_id=user_id)
            return to_domain_business_profile(django_profile)
        except BusinessProfile.DoesNotExist:
            return None

    def get_by_verification_id(
        self, verification_id: int
    ) -> DomainBusinessProfile | None:
        try:
            django_profile = BusinessProfile.objects.get(
                verification_id=verification_id
            )
            return to_domain_business_profile(django_profile)
        except BusinessProfile.DoesNotExist:
            return None


class DjangoBusinessVerificationRepository(IBusinessVerificationRepository):
    def create(
        self, verification: DomainBusinessVerification
    ) -> DomainBusinessVerification:
        try:
            verification.verification_provider = settings.BUSINESS_VERIFICATION_PROVIDER

            django_verification = BusinessVerification.objects.create(
                **from_domain_business_verification(verification)
            )
            return to_domain_business_verification(django_verification)

        except IntegrityError as e:
            logger.error(
                f"Integrity error during business verification creation for '{verification.business_email}': {e}"
            )
            raise ConflictError from e

        except Exception as e:
            logger.critical(
                f"Unhandled error during business verification creation for '{verification.business_email}': {e}"
            )
            raise BaseAPIException(
                "Business verification creation failed. Please try again later."
            )

    def update(
        self, verification: DomainBusinessVerification, **kwargs
    ) -> DomainBusinessVerification:
        try:
            django_verification = BusinessVerification.objects.get(id=verification.id)

            for key, value in kwargs.items():
                if hasattr(django_verification, key) and key in ["verification_status"]:
                    setattr(django_verification, key, value)

            django_verification.save()
            return to_domain_business_verification(django_verification)

        except Exception as e:
            logger.critical(
                f"Unhandled error during business verification update for '{verification.business_email}': {e}"
            )
            raise BaseAPIException(
                "Business verification update failed. Please try again later."
            ) from e

    def get_by_id(self, verification_id: int) -> DomainBusinessVerification | None:
        try:
            django_verification = BusinessVerification.objects.get(id=verification_id)
            return to_domain_business_verification(django_verification)
        except BusinessVerification.DoesNotExist:
            return None

    def get_by_user_id(self, user_id: int) -> DomainBusinessVerification | None:
        try:
            django_verification = BusinessVerification.objects.get(user_id=user_id)
            return to_domain_business_verification(django_verification)
        except BusinessVerification.DoesNotExist:
            return None
