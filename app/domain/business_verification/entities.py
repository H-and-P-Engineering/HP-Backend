from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Type
from uuid import UUID

from .enums import VerificationStatus


@dataclass
class BusinessProfile:
    user_id: int
    business_name: str
    business_email: str
    registration_number: str
    address: str | None = None
    phone_number: str | None = None
    website: str | None = None
    verification_id: int | None = None
    is_business_email_verified: bool = False
    id: int | None = None
    uuid: Type[UUID] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class BusinessVerification:
    user_id: int
    business_name: str
    business_email: str
    business_registration_number: str
    country_code: str = "NG"
    verification_provider: str | None = None
    verification_provider_reference: str | None = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    id: int | None = None
    uuid: Type[UUID] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class BusinessVerificationResult:
    success: bool
    provider_reference: str | None = None
    business_data: Dict[str, Any] | None = None
    error_message: str | None = None
