from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class CacheServiceAdapterInterface(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass


class EmailServiceAdapterInterface(ABC):
    @abstractmethod
    def send_verification_email(
        self, recipient_email: str, verification_link: str
    ) -> None:
        pass


class VerificationServiceAdapterInterface(ABC):
    @abstractmethod
    def generate_token(self) -> str:
        pass

    @abstractmethod
    def generate_email_verification_link(
        self, verification_uuid: UUID, verification_token: str
    ) -> str:
        pass


class EventPublisherInterface(ABC):
    @abstractmethod
    def publish(self, event: Any) -> None:
        pass
