from typing import Any, Sequence

from uuid6 import UUID
from rest_framework.exceptions import NotFound

from core.interfaces import BaseRepository
from .models import User, BlackListedToken


class UserRepository(BaseRepository[User]):
    async def get_by_uuid(self, uuid: str | UUID) -> User:
        try:
            return await User.objects.aget(uuid=uuid)
        except User.DoesNotExist:
            raise NotFound("User not found")

    async def get_by_email(self, email: str) -> User:
        try:
            return await User.objects.aget(email=email)
        except User.DoesNotExist:
            raise NotFound("User not found")

    async def create(self, **kwargs: Any) -> User:
        return await User.objects.acreate_user(**kwargs)

    async def update(self, uuid: str | UUID, update_data: dict[str, Any]) -> User:
        user = await self.get_by_uuid(uuid)
        for key, value in update_data.items():
            setattr(user, key, value)
        await user.asave()
        return user

    async def delete(self, uuid: str | UUID) -> None:
        user = await self.get_by_uuid(uuid)
        await user.adelete()

    async def list(self, **filters: Any) -> Sequence[User]:
        return [user async for user in User.objects.filter(**filters)]

    async def update_email_verification_status(self, user: User) -> User:
        user.is_email_verified = True
        await user.asave(update_fields=["is_email_verified"])
        await user.arefresh_from_db()
        return user


class BlackListedTokenRepository(BaseRepository[BlackListedToken]):
    async def get_by_uuid(self, uuid: str | UUID) -> BlackListedToken:
        try:
            return await BlackListedToken.objects.aget(id=uuid)
        except BlackListedToken.DoesNotExist:
            raise NotFound("Token not found")

    async def create(self, **kwargs: Any) -> BlackListedToken:
        token, _ = await BlackListedToken.objects.aget_or_create(**kwargs)
        return token

    async def update(
        self, uuid: str | UUID, update_data: dict[str, Any]
    ) -> BlackListedToken:
        token = await self.get_by_uuid(uuid)
        for key, value in update_data.items():
            setattr(token, key, value)
        await token.asave()
        return token

    async def delete(self, uuid: str | UUID) -> None:
        # Check if uuid is an instance of BlackListedToken since old delete took the object
        if isinstance(uuid, BlackListedToken):
            await uuid.adelete()
            return

        token = await self.get_by_uuid(uuid)
        await token.adelete()

    async def list(self, **filters: Any) -> Sequence[BlackListedToken]:
        return [token async for token in BlackListedToken.objects.filter(**filters)]

    async def check_exists(self, jti: str) -> bool:
        return await BlackListedToken.is_blacklisted(access_token=jti)
