from typing import Any, Sequence

from django.db import IntegrityError
from loguru import logger
from rest_framework.exceptions import NotFound
from uuid6 import UUID

from core.exceptions import BaseAPIException, ConflictError
from core.interfaces import BaseRepository
from .models import BusinessProfile, BusinessVerification


class BusinessProfileRepository(BaseRepository[BusinessProfile]):
    async def get_by_uuid(self, uuid: str | UUID) -> BusinessProfile:
        try:
            return await BusinessProfile.objects.aget(uuid=uuid)
        except BusinessProfile.DoesNotExist:
            raise NotFound("Business profile not found")

    async def create(self, **kwargs: Any) -> BusinessProfile:
        try:
            return await BusinessProfile.objects.acreate(**kwargs)
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
                "Integrity error during business profile creation", error=str(e)
            )
            raise ConflictError from e

        except Exception as e:
            logger.critical(
                "Unhandled error during business profile creation", error=str(e)
            )
            raise BaseAPIException(
                "Business profile creation failed. Please try again later."
            ) from e

    async def update(
        self, uuid: str | UUID, update_data: dict[str, Any]
    ) -> BusinessProfile:
        try:
            profile = await self.get_by_uuid(uuid)
            for key, value in update_data.items():
                if hasattr(profile, key) and key not in [
                    "user_id",
                    "uuid",
                    "id",
                    "created_at",
                ]:
                    setattr(profile, key, value)

            await profile.asave()
            await profile.arefresh_from_db()
            return profile

        except NotFound:
            raise
        except Exception as e:
            logger.critical(
                "Unhandled error during business profile update", error=str(e)
            )
            raise BaseAPIException(
                "Business profile update failed. Please try again later."
            ) from e

    async def delete(self, uuid: str | UUID) -> None:
        profile = await self.get_by_uuid(uuid)
        await profile.adelete()

    async def list(self, **filters: Any) -> Sequence[BusinessProfile]:
        return [profile async for profile in BusinessProfile.objects.filter(**filters)]

    async def get_by_user_id(self, user_id: int) -> BusinessProfile | None:
        try:
            return await BusinessProfile.objects.aget(user_id=user_id)
        except BusinessProfile.DoesNotExist:
            return None

    async def get_by_verification_id(
        self, verification_id: int
    ) -> BusinessProfile | None:
        try:
            return await BusinessProfile.objects.aget(verification_id=verification_id)
        except BusinessProfile.DoesNotExist:
            return None


class BusinessVerificationRepository(BaseRepository[BusinessVerification]):
    async def get_by_uuid(self, uuid: str | UUID | int) -> BusinessVerification:
        try:
            return await BusinessVerification.objects.aget(uuid=uuid)
        except BusinessVerification.DoesNotExist:
            raise NotFound("Business verification not found")

    async def create(self, **kwargs: Any) -> BusinessVerification:
        try:
            return await BusinessVerification.objects.acreate(**kwargs)

        except IntegrityError as e:
            logger.error(
                "Integrity error during business verification creation", error=str(e)
            )
            raise ConflictError from e

        except Exception as e:
            logger.critical(
                "Unhandled error during business verification creation",
                error=str(e),
            )
            raise BaseAPIException(
                "Business verification creation failed. Please try again later."
            ) from e

    async def update(
        self, uuid: str | UUID | int, update_data: dict[str, Any]
    ) -> BusinessVerification:
        try:
            verification = await self.get_by_uuid(uuid)
            for key, value in update_data.items():
                if hasattr(verification, key) and key in [
                    "verification_status",
                    "verification_provider_reference",
                ]:
                    setattr(verification, key, value)

            await verification.asave()
            await verification.arefresh_from_db()
            return verification

        except NotFound:
            raise
        except Exception as e:
            logger.critical(
                "Unhandled error during business verification update", error=str(e)
            )
            raise BaseAPIException(
                "Business verification update failed. Please try again later."
            ) from e

    async def delete(self, uuid: str | UUID | int) -> None:
        verification = await self.get_by_uuid(uuid)
        await verification.adelete()

    async def list(self, **filters: Any) -> Sequence[BusinessVerification]:
        return [v async for v in BusinessVerification.objects.filter(**filters)]

    async def get_by_id(self, verification_id: int) -> BusinessVerification | None:
        try:
            return await BusinessVerification.objects.aget(id=verification_id)
        except BusinessVerification.DoesNotExist:
            return None

    async def get_by_user_id(self, user_id: int) -> BusinessVerification | None:
        try:
            return await BusinessVerification.objects.aget(user_id=user_id)
        except BusinessVerification.DoesNotExist:
            return None
