from datetime import UTC, datetime

from apps.business_verification.application.ports import (
    BusinessProfileRepositoryInterface,
    BusinessVerificationRepositoryInterface,
    BusinessVerificationServiceInterface,
)
from apps.business_verification.domain.enums import VerificationStatus
from apps.business_verification.domain.events import (
    BusinessEmailVerificationSuccessfulEvent,
    BusinessVerificationEmailEvent,
    BusinessVerificationFailedEvent,
    BusinessVerificationRequestedEvent,
    BusinessVerificationSuccessfulEvent,
)
from apps.business_verification.domain.models import (
    BusinessProfile,
    BusinessVerification,
)
from apps.users.application.ports import UserRepositoryInterface
from apps.users.domain.enums import UserType
from core.application.exceptions import BusinessRuleException
from core.application.ports import CacheServiceAdapterInterface, EventPublisherInterface


class CreateBusinessProfileRule:
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        business_profile_repository: BusinessProfileRepositoryInterface,
    ) -> None:
        self._user_repository = user_repository
        self._business_profile_repository = business_profile_repository

    def execute(
        self,
        user_id: int,
        business_name: str,
        business_email: str,
        registration_number: str,
        address: str | None = None,
        phone_number: str | None = None,
        website: str | None = None,
    ) -> BusinessProfile:
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise BusinessRuleException("User not found")

        if user.user_type in [UserType.CLIENT, UserType.ADMIN]:
            raise BusinessRuleException("User does not need business profile")

        existing_profile = self._business_profile_repository.get_by_user_id(user_id)
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

        return self._business_profile_repository.create(profile)


class InitiateBusinessVerificationRule:
    def __init__(
        self,
        business_profile_repository: BusinessProfileRepositoryInterface,
        business_verification_repository: BusinessVerificationRepositoryInterface,
        verification_service: BusinessVerificationServiceInterface,
        user_repository: UserRepositoryInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._business_profile_repository = business_profile_repository
        self._business_verification_repository = business_verification_repository
        self._verification_service = verification_service
        self._user_repository = user_repository
        self._event_publisher = event_publisher

    def execute(
        self,
        user_id: int,
        country_code: str = "NG",
    ) -> BusinessVerification:
        profile = self._business_profile_repository.get_by_user_id(user_id)
        if not profile:
            raise BusinessRuleException("Business profile not found for user")

        existing_verification = self._business_verification_repository.get_by_user_id(
            user_id
        )
        if existing_verification:
            if (
                existing_verification.verification_status
                == VerificationStatus.SUCCESSFUL
            ):
                raise BusinessRuleException("Business verification already successful")

            self._event_publisher.publish(
                BusinessVerificationRequestedEvent(
                    verification_id=existing_verification.id
                )
            )

            existing_verification.verification_status = VerificationStatus.PENDING
            return existing_verification

        verification = BusinessVerification(
            user_id=user_id,
            business_registration_number=profile.registration_number,
            business_name=profile.business_name,
            business_email=profile.business_email,
            country_code=country_code,
        )

        created_verification = self._business_verification_repository.create(
            verification
        )

        self._event_publisher.publish(
            BusinessVerificationRequestedEvent(verification_id=created_verification.id)
        )

        return created_verification


class ProcessBusinessVerificationRule:
    def __init__(
        self,
        business_profile_repository: BusinessProfileRepositoryInterface,
        business_verification_repository: BusinessVerificationRepositoryInterface,
        verification_service: BusinessVerificationServiceInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._business_profile_repository = business_profile_repository
        self._business_verification_repository = business_verification_repository
        self._verification_service = verification_service
        self._event_publisher = event_publisher

    def execute(self, verification_id: int) -> None:
        verification = self._business_verification_repository.get_by_id(verification_id)
        if not verification:
            return

        self._business_verification_repository.update(
            verification, verification_status=VerificationStatus.IN_PROGRESS
        )

        try:
            result = self._verification_service.verify_business(
                registration_number=verification.business_registration_number,
                country_code=verification.country_code,
                business_email=verification.business_email,
            )

            if result.success:
                self._business_verification_repository.update(
                    verification,
                    verification_status=VerificationStatus.SUCCESSFUL,
                    provider_reference=result.provider_reference,
                    updated_at=datetime.now(tz=UTC),
                )

                self._event_publisher.publish(
                    BusinessVerificationSuccessfulEvent(
                        verification_id=verification.id,
                        user_id=verification.user_id,
                        business_name=verification.business_name,
                        business_email=verification.business_email,
                    )
                )

                self._event_publisher.publish(
                    BusinessVerificationEmailEvent(verification.id)
                )
            else:
                self._business_verification_repository.update(
                    verification,
                    verification_status=VerificationStatus.FAILED,
                    updated_at=datetime.now(tz=UTC),
                )

                self._event_publisher.publish(
                    BusinessVerificationFailedEvent(
                        verification_id=verification.id,
                        user_id=verification.user_id,
                        business_name=verification.business_name,
                        business_email=verification.business_email,
                        error_reason=result.error_message,
                    )
                )
        except Exception as e:
            self._business_verification_repository.update(
                verification,
                verification_status=VerificationStatus.FAILED,
                updated_at=datetime.now(tz=UTC),
            )

            self._event_publisher.publish(
                BusinessVerificationFailedEvent(
                    verification_id=verification.id,
                    user_id=verification.user_id,
                    business_name=verification.business_name,
                    business_email=verification.business_email,
                    error_reason=f"Verification service error: {str(e)}",
                )
            )


class VerifyBusinessEmailRule:
    def __init__(
        self,
        cache_service: CacheServiceAdapterInterface,
        business_profile_repository: BusinessProfileRepositoryInterface,
        business_verification_repository: BusinessVerificationRepositoryInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._cache_service = cache_service
        self._business_profile_repository = business_profile_repository
        self._business_verification_repository = business_verification_repository
        self._event_publisher = event_publisher

    def execute(self, verification_uuid: str, token: str) -> None:
        cached_data = self._cache_service.get(f"email_verify_{verification_uuid}")
        if cached_data:
            cached_id, cached_token = cached_data
        else:
            raise BusinessRuleException(
                "Business email verification failed. Verification session is invalid or expired."
            )

        business_profile = self._business_profile_repository.get_by_verification_id(
            cached_id
        )

        if business_profile and business_profile.is_business_email_verified:
            raise BusinessRuleException(
                "Business email verification failed. Business email is already verified."
            )

        verification = self._business_verification_repository.get_by_id(cached_id)

        if (
            not verification
            or str(verification.uuid) != str(verification_uuid)
            or cached_token != token
        ):
            raise BusinessRuleException(
                "Business email verification failed. Provided verification id or verification token is invalid."
            )

        self._event_publisher.publish(
            BusinessEmailVerificationSuccessfulEvent(verification.id)
        )


class RequestBusinessEmailVerificationRule:
    def __init__(
        self,
        cache_service: CacheServiceAdapterInterface,
        business_verification_repository: BusinessVerificationRepositoryInterface,
        event_publisher: EventPublisherInterface,
    ) -> None:
        self._cache_service = cache_service
        self._business_verification_repository = business_verification_repository
        self._event_publisher = event_publisher

    def execute(self, business_email: str, user_id) -> None:
        if self._cache_service.get(f"{business_email}_verified"):
            raise BusinessRuleException(
                "Business email verification request failed. Business email is already verified."
            )

        verification = self._business_verification_repository.get_by_user_id(user_id)

        if not verification:
            raise BusinessRuleException("Business verification not found for user")

        if verification.verification_status != VerificationStatus.SUCCESSFUL:
            raise BusinessRuleException(
                "Business email verification request failed. Business verification was not successful."
            )

        self._event_publisher.publish(BusinessVerificationEmailEvent(verification.id))
