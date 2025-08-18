from abc import ABC, abstractmethod

from apps.business_verification.domain.models import (
    BusinessProfile,
    BusinessVerification,
    BusinessVerificationResult,
)


class BusinessProfileRepositoryInterface(ABC):
    @abstractmethod
    def create(self, profile: BusinessProfile) -> BusinessProfile:
        pass

    @abstractmethod
    def update(self, profile: BusinessProfile, **kwargs) -> BusinessProfile:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> BusinessProfile | None:
        pass

    @abstractmethod
    def get_by_verification_id(self, verification_id: int) -> BusinessProfile | None:
        pass


class BusinessVerificationRepositoryInterface(ABC):
    @abstractmethod
    def create(self, verification: BusinessVerification) -> BusinessVerification:
        pass

    @abstractmethod
    def update(
        self, verification: BusinessVerification, **kwargs
    ) -> BusinessVerification:
        pass

    @abstractmethod
    def get_by_id(self, verification_id: int) -> BusinessVerification | None:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> BusinessVerification | None:
        pass


class BusinessVerificationServiceInterface(ABC):
    @abstractmethod
    def verify_business(
        self,
        registration_number: str,
        business_email: str,
        country_code: str = "NG",
    ) -> BusinessVerificationResult:
        pass
