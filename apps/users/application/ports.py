from abc import ABC, abstractmethod
from typing import Any

from apps.users.domain.models import User


class UserRepositoryInterface(ABC):
    @abstractmethod
    def create(self, user: User) -> User:
        pass

    @abstractmethod
    def update(self, user: User, **kwargs) -> User:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> User:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User:
        pass

    @abstractmethod
    def get_or_create_social(self, request: Any) -> User:
        pass
