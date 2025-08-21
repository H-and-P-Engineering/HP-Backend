from typing import Any

from app.infrastructure.users.events import UserEvent


class UserVerificationEmailEvent(UserEvent):
    pass


class UserEmailVerifiedEvent(UserEvent):
    pass


class UserLogoutEvent(UserEvent):
    def __init__(self, user_id: int, token: Any) -> None:
        super().__init__(user_id)
        self.token = token
