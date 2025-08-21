from typing import Any, Callable

from app.application.business_verification.ports import (
    IBusinessProfileRepository,
    IBusinessVerificationRepository,
)
from app.application.users.ports import IUserRepository
from app.core.exceptions import BusinessRuleException
from app.domain.business_verification.entities import (
    BusinessProfile,
    BusinessVerification,
)
from app.domain.business_verification.enums import VerificationStatus
from app.domain.users.enums import UserType


class CreateBusinessProfileRule:
    def __init__(
        self,
        user_repository: IUserRepository,
        business_profile_repository: IBusinessProfileRepository,
    ) -> None:
        self.user_repository = user_repository
        self.business_profile_repository = business_profile_repository

    def __call__(
        self,
        user_id: int,
        business_name: str,
        business_email: str,
        registration_number: str,
        address: str | None = None,
        phone_number: str | None = None,
        website: str | None = None,
    ) -> BusinessProfile:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise BusinessRuleException("User not found")

        if user.user_type in [UserType.CLIENT, UserType.ADMIN]:
            raise BusinessRuleException("User does not need business profile")

        existing_profile = self.business_profile_repository.get_by_user_id(user_id)
        if existing_profile:
            raise BusinessRuleException("Business profile already exists for this user")

        profile = BusinessProfile(
            user_id=user_id,
            business_name=business_name,
            business_email=business_email,
            registration_number=registration_number.upper().strip(),
            address=address,
            phone_number=phone_number,
            website=website,
        )

        return self.business_profile_repository.create(profile)


class InitiateBusinessVerificationRule:
    def __init__(
        self,
        business_profile_repository: IBusinessProfileRepository,
        business_verification_repository: IBusinessVerificationRepository,
        user_repository: IUserRepository,
        event_publisher: Callable[[Any], str],
    ) -> None:
        self.business_profile_repository = business_profile_repository
        self.business_verification_repository = business_verification_repository

        self.user_repository = user_repository
        self.event_publisher = event_publisher

    def __call__(
        self,
        user_id: int,
        country_code: str = "NG",
        event: Callable[[Any], Any] | None = None,
    ) -> BusinessVerification:
        profile = self.business_profile_repository.get_by_user_id(user_id)
        if not profile:
            raise BusinessRuleException("Business profile not found for user")

        verification_instance = None

        existing_verification = self.business_verification_repository.get_by_user_id(
            user_id
        )
        if existing_verification:
            if (
                existing_verification.verification_status
                == VerificationStatus.SUCCESSFUL
            ):
                raise BusinessRuleException("Business verification already successful")

            existing_verification.verification_status = VerificationStatus.PENDING
            verification_instance = existing_verification
        else:
            verification = BusinessVerification(
                user_id=user_id,
                business_registration_number=profile.registration_number,
                business_name=profile.business_name,
                business_email=profile.business_email,
                country_code=country_code,
            )

            created_verification = self.business_verification_repository.create(
                verification
            )

            self.business_profile_repository.update(
                profile, verification_id=created_verification.id
            )

            verification_instance = created_verification

        if event:
            self.event_publisher.publish(event(verification_instance.id))

        return verification_instance


class ProcessBusinessVerificationRule:
    def __init__(
        self,
        business_profile_repository: IBusinessProfileRepository,
        business_verification_repository: IBusinessVerificationRepository,
        verification_service: Callable[[Any], str],
        event_publisher: Callable[[Any], str],
    ) -> None:
        self.business_profile_repository = business_profile_repository
        self.business_verification_repository = business_verification_repository
        self.verification_service = verification_service
        self.event_publisher = event_publisher

    def __call__(
        self, verification_id: int, event: Callable[[Any], Any] | None = None
    ) -> None:
        verification = self.business_verification_repository.get_by_id(verification_id)
        if not verification:
            return

        self.business_verification_repository.update(
            verification, verification_status=VerificationStatus.IN_PROGRESS
        )

        try:
            result = self.verification_service.verify_business(
                registration_number=verification.business_registration_number,
                country_code=verification.country_code,
                business_email=verification.business_email,
            )

            if result.success:
                if event:
                    self.event_publisher.publish(
                        event(
                            verification.id,
                            success=True,
                            user_id=verification.user_id,
                            business_name=verification.business_name,
                            business_email=verification.business_email,
                        )
                    )

                self.business_verification_repository.update(
                    verification,
                    verification_status=VerificationStatus.SUCCESSFUL,
                    provider_reference=result.provider_reference,
                )
            else:
                self.business_verification_repository.update(
                    verification,
                    verification_status=VerificationStatus.FAILED,
                )

                if event:
                    self.event_publisher.publish(
                        event(
                            verification.id,
                            success=False,
                            user_id=verification.user_id,
                            business_name=verification.business_name,
                            business_email=verification.business_email,
                            error_reason=result.error_message,
                        )
                    )
        except Exception:
            self.business_verification_repository.update(
                verification,
                verification_status=VerificationStatus.FAILED,
            )

            if event:
                self.event_publisher.publish(
                    event(
                        verification.id,
                        success=False,
                        user_id=verification.user_id,
                        business_name=verification.business_name,
                        business_email=verification.business_email,
                        error_reason="An internal error occurred",
                    )
                )


class VerifyBusinessEmailRule:
    def __init__(
        self,
        cache_service: Callable[[Any], str],
        business_profile_repository: IBusinessProfileRepository,
        business_verification_repository: IBusinessVerificationRepository,
        event_publisher: Callable[[Any], str],
    ) -> None:
        self.cache_service = cache_service
        self.business_profile_repository = business_profile_repository
        self.business_verification_repository = business_verification_repository
        self.event_publisher = event_publisher

    def __call__(
        self,
        verification_uuid: str,
        token: str,
        event: Callable[[Any], Any] | None = None,
    ) -> None:
        cached_data = self.cache_service.get(f"email_verify_{verification_uuid}")
        if cached_data:
            cached_id, cached_token = cached_data
        else:
            raise BusinessRuleException(
                "Business email verification failed. Verification session is invalid or expired."
            )

        business_profile = self.business_profile_repository.get_by_verification_id(
            cached_id
        )

        if business_profile and business_profile.is_business_email_verified:
            raise BusinessRuleException(
                "Business email verification failed. Business email is already verified."
            )

        verification = self.business_verification_repository.get_by_id(cached_id)

        if (
            not verification
            or str(verification.uuid) != str(verification_uuid)
            or cached_token != token
        ):
            raise BusinessRuleException(
                "Business email verification failed. Provided verification id or verification token is invalid."
            )

        if event:
            self.event_publisher.publish(event(verification.id))


class RequestBusinessEmailVerificationRule:
    def __init__(
        self,
        cache_service: Callable[[Any], Any],
        business_verification_repository: IBusinessVerificationRepository,
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.cache_service = cache_service
        self.business_verification_repository = business_verification_repository
        self.event_publisher = event_publisher

    def __call__(
        self, business_email: str, user_id, event: Callable[[Any], Any] | None = None
    ) -> None:
        if self.cache_service.get(f"{business_email}_verified"):
            raise BusinessRuleException(
                "Business email verification request failed. Business email is already verified."
            )

        verification = self.business_verification_repository.get_by_user_id(user_id)

        if not verification:
            raise BusinessRuleException("Business verification not found for user")

        if verification.verification_status != VerificationStatus.SUCCESSFUL:
            raise BusinessRuleException(
                "Business email verification request failed. Business verification was not successful."
            )

        if event:
            self.event_publisher.publish(event(verification.id))
