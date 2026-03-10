from abc import ABC, abstractmethod
from typing import Any, Sequence, Protocol, TypeVar, Generic

from uuid6 import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_uuid(self, uuid: str | UUID) -> T:
        pass

    @abstractmethod
    async def create(self, **kwargs: Any) -> T:
        pass

    @abstractmethod
    async def update(self, uuid: str | UUID, update_data: dict[str, Any]) -> T:
        pass

    @abstractmethod
    async def delete(self, uuid: str | UUID) -> None:
        pass

    @abstractmethod
    async def list(self, **filters: Any) -> Sequence[T]:
        pass


class IEmailService(Protocol):
    def send_template_email(
        self,
        subject: str,
        template_name: str,
        context: dict,
        recipient_list: Sequence[str],
        from_email: str | None = None,
    ) -> None: ...

    def send_standard_email(
        self,
        email_type: Any,  # Using Any to avoid circular import with core.enums
        context: dict,
        recipient_list: Sequence[str],
        subject_prefix: str = "",
        from_email: str | None = None,
    ) -> None: ...
