from abc import ABC, abstractmethod
from typing import Any

from apps.users.domain.models import User as DomainUser


class UserRepositoryInterface(ABC):
    @abstractmethod
    def create(self, user: DomainUser) -> DomainUser:
        pass

    @abstractmethod
    def update(self, user: DomainUser, **kwargs) -> DomainUser:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> DomainUser:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> DomainUser:
        pass

    @abstractmethod
    def get_or_create_social(self, request: Any) -> DomainUser:
        pass
