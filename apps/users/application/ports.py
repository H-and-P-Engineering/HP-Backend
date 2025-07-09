from abc import ABC, abstractmethod

from apps.users.domain.models import User as DomainUser
from typing import Any


class UserRepositoryInterface(ABC):
    @abstractmethod
    def create(self, user: DomainUser) -> DomainUser:
        pass

    @abstractmethod
    def create_social(self, user: DomainUser) -> Any:
        pass

    @abstractmethod
    def update(self, user: DomainUser, return_raw: bool = True, **kwargs) -> DomainUser:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> DomainUser | None:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> DomainUser | None:
        pass
