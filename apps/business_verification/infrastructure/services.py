import requests
from django.conf import settings

from apps.business_verification.application.ports import (
    BusinessVerificationServiceInterface,
)
from apps.business_verification.domain.models import BusinessVerificationResult
from core.infrastructure.logging.base import logger


class YouVerifyAdapter(BusinessVerificationServiceInterface):
    def __init__(self):
        self.base_url = getattr(
            settings, "YOUVERIFY_BASE_URL", "https://api.sandbox.youverify.co"
        )
        self.api_token = getattr(settings, "YOUVERIFY_API_TOKEN", "")

    def verify_business(
        self,
        business_email: str,
        registration_number: str,
        country_code: str = "NG",
    ) -> BusinessVerificationResult:
        try:
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
                    data.get("success")
                    and data.get("data", {}).get("status") == "found"
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

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during business verification: {e}")
            return BusinessVerificationResult(
                success=False, error_message="Network error during verification"
            )
        except Exception as e:
            logger.error(f"Unexpected error during business verification: {e}")
            return BusinessVerificationResult(
                success=False, error_message="Unexpected error during verification"
            )
