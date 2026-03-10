import json
from dataclasses import dataclass
from typing import Any

import httpx
from django.conf import settings
from loguru import logger

from core.exceptions import BadRequestError
from core.services import BaseCacheService, EmailService
from .models import (
    BusinessProfile,
    BusinessVerification,
    VerificationStatus,
)
from core.container import container
from .repositories import (
    BusinessProfileRepository,
    BusinessVerificationRepository,
)
from users.repositories import UserRepository


@dataclass
class BusinessVerificationResult:
    success: bool
    provider_reference: str | None = None
    business_data: dict[str, Any] | None = None
    error_message: str | None = None


class BusinessCacheService(BaseCacheService):
    def __init__(self) -> None:
        super().__init__(prefix="business", timeout=settings.CACHE_BUSINESS_TIMEOUT)

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        cached = self.get(f"profile:{user_id}")
        if cached:
            return json.loads(cached)
        return None

    def set_profile(self, user_id: int, profile_data: dict[str, Any]) -> None:
        self.set(f"profile:{user_id}", json.dumps(profile_data))

    def invalidate_profile(self, user_id: int) -> None:
        self.delete(f"profile:{user_id}")

    def get_verification(self, user_id: int) -> dict[str, Any] | None:
        cached = self.get(f"verification:{user_id}")
        if cached:
            return json.loads(cached)
        return None

    def set_verification(self, user_id: int, verification_data: dict[str, Any]) -> None:
        self.set(f"verification:{user_id}", json.dumps(verification_data))

    def invalidate_verification(self, user_id: int) -> None:
        self.delete(f"verification:{user_id}")


class YouVerifyService:
    def __init__(self) -> None:
        self.base_url = getattr(
            settings, "YOUVERIFY_BASE_URL", "https://api.sandbox.youverify.co"
        )
        self.api_token = getattr(settings, "YOUVERIFY_API_TOKEN", "")

    async def verify_business(
        self,
        business_email: str,
        registration_number: str,
        country_code: str = "NG",
    ) -> BusinessVerificationResult:
        if not self.api_token:
            logger.error("YouVerify API token not configured")
            return BusinessVerificationResult(
                success=False, error_message="Verification service not configured"
            )

        url = f"{self.base_url}/v2/api/verifications/global/company-advance-check"
        headers = {"Content-Type": "application/json", "token": self.api_token}
        payload = {
            "registrationNumber": registration_number,
            "countryCode": country_code,
            "isConsent": True,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json=payload, headers=headers, timeout=30
                )

            if response.status_code == 200:
                data = response.json()
                if (
                    data.get("success")
                    and data.get("data", {}).get("status") == "found"
                ):
                    return BusinessVerificationResult(
                        success=True,
                        provider_reference=data.get("data", {}).get("id"),
                        business_data=data.get("data", {}),
                    )
                else:
                    return BusinessVerificationResult(
                        success=False,
                        error_message="Business not found or verification failed",
                    )
            else:
                logger.error(
                    "YouVerify API error",
                    status_code=response.status_code,
                    response_body=response.text[:200],
                )
                return BusinessVerificationResult(
                    success=False, error_message=f"API error: {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("Request error during business verification", error=str(e))
            return BusinessVerificationResult(
                success=False, error_message="Network error during verification"
            )
        except Exception as e:
            logger.error("Unhandled error during business verification", error=str(e))
            return BusinessVerificationResult(
                success=False, error_message="Unexpected error during verification"
            )


class BusinessProfileService:
    def __init__(
        self,
        cache: BusinessCacheService | None = None,
        verification_api: YouVerifyService | None = None,
        repository: BusinessProfileRepository | None = None,
    ) -> None:
        self.cache = cache or BusinessCacheService()
        self.verification_api = verification_api or YouVerifyService()
        self.repository = repository or container.business_profile_repository()

    async def create_profile(
        self,
        user_id: int,
        business_name: str,
        business_email: str,
        registration_number: str,
        address: str | None = None,
        phone_number: str | None = None,
        website: str | None = None,
    ) -> BusinessProfile:
        profile = await self.repository.create(
            user_id=user_id,
            business_name=business_name,
            business_email=business_email,
            registration_number=registration_number,
            address=address,
            phone_number=phone_number,
            website=website,
        )
        return profile

    async def get_profile_by_user_id(self, user_id: int) -> BusinessProfile | None:
        return await self.repository.get_by_user_id(user_id)

    async def update_profile(
        self, profile: BusinessProfile, **kwargs: Any
    ) -> BusinessProfile:
        return await self.repository.update(profile, **kwargs)


class BusinessVerificationService:
    def __init__(
        self,
        cache: BusinessCacheService | None = None,
        verification_api: YouVerifyService | None = None,
        profile_service: BusinessProfileService | None = None,
        email_service: EmailService | None = None,
        repository: BusinessVerificationRepository | None = None,
        profile_repo: BusinessProfileRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self.cache = cache or BusinessCacheService()
        self.verification_api = verification_api or YouVerifyService()
        self.profile_service = profile_service or container.business_profile_service()
        self.email_service = email_service or container.email_service()
        self.repository = repository or container.business_verification_repository()
        self.profile_repository = (
            profile_repo or container.business_profile_repository()
        )
        self.user_repository = user_repo or container.user_repository()

    async def initiate_verification(
        self,
        user_id: int,
        country_code: str = "NG",
    ) -> BusinessVerification:
        profile = await self.profile_service.get_profile_by_user_id(user_id)
        if not profile:
            raise BadRequestError(
                "Business profile not found. Please create a profile first."
            )

        existing = await self.repository.get_by_user_id(user_id)
        if existing and existing.verification_status == VerificationStatus.SUCCESSFUL:
            raise BadRequestError("Business already verified.")

        verification = await self.repository.create(
            user_id=user_id,
            business_registration_number=profile.registration_number,
            business_name=profile.business_name,
            business_email=profile.business_email,
            country_code=country_code,
            verification_provider=getattr(
                settings, "BUSINESS_VERIFICATION_PROVIDER", "youverify"
            ),
            verification_status=VerificationStatus.IN_PROGRESS,
        )

        result = await self.verification_api.verify_business(
            business_email=profile.business_email,
            registration_number=profile.registration_number,
            country_code=country_code,
        )

        if result.success:
            verification = await self.repository.update(
                verification,
                verification_status=VerificationStatus.SUCCESSFUL,
                verification_provider_reference=result.provider_reference,
            )
            await self.profile_repository.update(
                profile, verification_id=verification.id
            )

            self.cache.invalidate_verification(user_id)
            self.cache.invalidate_profile(user_id)

            self.email_service.send_business_verification_success_email(
                recipient_email=profile.business_email,
                business_name=profile.business_name,
                registration_number=profile.registration_number,
                provider_reference=result.provider_reference,
            )
        else:
            verification = await self.repository.update(
                verification,
                verification_status=VerificationStatus.FAILED,
            )

            self.cache.invalidate_verification(user_id)

            self.email_service.send_business_verification_failed_email(
                recipient_email=profile.business_email,
                business_name=profile.business_name,
                registration_number=profile.registration_number,
                error_reason=result.error_message,
            )

        return verification

    async def get_verification_status(
        self, user_id: int
    ) -> BusinessVerification | None:
        return await self.repository.get_by_user_id(user_id)

    async def send_business_email_verification(self, user_id: int) -> None:
        profile = await self.profile_service.get_profile_by_user_id(user_id)
        if not profile:
            raise BadRequestError("Business profile not found.")

        user = await self.user_repository.get_by_id(user_id)
        verification_link = container.verification_service().run(str(user.uuid))

        self.email_service.send_business_verification_email(
            recipient_email=profile.business_email,
            verification_link=verification_link,
            business_name=profile.business_name,
            registration_number=profile.registration_number,
        )

    async def verify_business_email(
        self, user_uuid: str, verification_token: str
    ) -> BusinessProfile:
        container.verification_service().validate_token(
            user_uuid=user_uuid,
            token=verification_token,
        )

        user = await self.user_repository.get_by_uuid(user_uuid)
        profile = await self.profile_repository.get_by_user_id(user.id)

        if not profile:
            raise BadRequestError("Business profile not found.")

        if profile.is_business_email_verified:
            raise BadRequestError("Business email already verified.")

        profile = await self.profile_repository.update(
            profile, is_business_email_verified=True
        )
        return profile
