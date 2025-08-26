from typing import Any, Callable

from app.application.users.ports import IUserRepository
from app.core.exceptions import BusinessRuleException
from app.domain.users.entities import User


class UpdateUserTypeRule:
    def __init__(
        self, user_repository: IUserRepository, event_publisher: Callable[[Any], Any]
    ) -> None:
        self.user_repository = user_repository
        self.event_publisher = event_publisher

    def __call__(
        self, email: str, user_type: str, event: Callable[[Any], Any] | None = None
    ) -> None:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise BusinessRuleException(
                "User type update failed. Provided email is invalid."
            )

        if event:
            self.event_publisher.publish(event(user.id, user_type=user_type))


class UpdateUserDataRule:
    def __init__(
        self,
        user_repository: IUserRepository,
        hash_password: Callable[[Any], Any],
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.user_repository = user_repository
        self.hash_password = hash_password
        self.event_publisher = event_publisher

    def __call__(
        self,
        user_id: int,
        event: Callable[[Any], Any] | None = None,
        **kwargs,
    ) -> User:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise BusinessRuleException(
                "Social registration update failed. Provided email is invalid."
            )

        update_data = {**kwargs}

        if update_data.get("password"):
            update_data["password"] = self.hash_password(update_data["password"])

        if event:
            self.event_publisher.publish(event(user.id, **update_data))

        for key, value in update_data.items():
            if (
                hasattr(user, key)
                and key not in ["password_hash", "created_at"]
                and value not in ["ADMIN"]
            ):
                setattr(user, key, value)

        user.is_new = False

        return user
