import requests
from django.conf import settings
from loguru import logger

from app.core.exceptions import BaseAPIException
from app.domain.business_verification.entities import BusinessVerificationResult


class BusinessVerificationService:
    def __init__(self) -> None:
        self._configure_provider()

    def _configure_provider(self):
        if settings.BUSINESS_VERIFICATION_PROVIDER == "youverify":
            self.provider = "youverify"
            self.base_url = getattr(
                settings, "YOUVERIFY_BASE_URL", "https://api.sandbox.youverify.co"
            )
            self.api_token = getattr(settings, "YOUVERIFY_API_TOKEN", "")

    def _get_youverify_response(
        self, business_email, registration_number, country_code
    ):
        url = f"{self.base_url}/v2/api/verifications/global/company-advance-check"
        headers = {"Content-Type": "application/json", "token": self.api_token}
        payload = {
            "registrationNumber": registration_number,
            "countryCode": country_code,
            "isConsent": True,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if (
                data.get("success") and data.get("data", {}).get("status") == "found"
                # and data.get("data", {}).get("email") == business_email
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
                f"YouVerify API error: {response.status_code} - {response.text}"
            )
            return BusinessVerificationResult(
                success=False, error_message=f"API error: {response.status_code}"
            )

    def verify_business(
        self,
        business_email: str,
        registration_number: str,
        country_code: str = "NG",
    ) -> BusinessVerificationResult:
        if self.provider == "youverify":
            try:
                return self._get_youverify_response(
                    business_email, registration_number, country_code
                )
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error during business verification: {e}")
                return BusinessVerificationResult(
                    success=False, error_message="Network error during verification"
                )
            except Exception as e:
                logger.error(f"Unhandled error during business verification: {e}")
                return BusinessVerificationResult(
                    success=False, error_message="Unexpected error during verification"
                )

        logger.error(f"Business verification provider missing")
        raise BaseAPIException("Business verification failed. Please try again later.")
