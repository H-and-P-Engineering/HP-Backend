from typing import Protocol

from app.domain.business_verification.entities import (
    BusinessProfile,
    BusinessVerification,
)


class IBusinessProfileRepository(Protocol):
    def create(self, profile: BusinessProfile) -> BusinessProfile: ...

    def update(self, profile: BusinessProfile, **kwargs) -> BusinessProfile: ...

    def get_by_user_id(self, user_id: int) -> BusinessProfile | None: ...

    def get_by_verification_id(
        self, verification_id: int
    ) -> BusinessProfile | None: ...


class IBusinessVerificationRepository(Protocol):
    def create(self, verification: BusinessVerification) -> BusinessVerification: ...

    def update(
        self, verification: BusinessVerification, **kwargs
    ) -> BusinessVerification: ...

    def get_by_id(self, verification_id: int) -> BusinessVerification | None: ...

    def get_by_user_id(self, user_id: int) -> BusinessVerification | None: ...
