from typing import Any, Callable

from app.application.users.ports import IUserRepository
from app.core.exceptions import BusinessRuleException


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
