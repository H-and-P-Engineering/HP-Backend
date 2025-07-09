from typing import Any, Dict

from apps.users.domain.events import UserEvent


class UserVerificationEmailEvent(UserEvent):
    pass


class UserEmailVerifiedEvent(UserEvent):
    pass


class UserUpdateEvent(UserEvent):
    def __init__(self, update_fields: Dict[str, Any], *args, **kwargs) -> None:
        self.update_fields = update_fields
        super().__init__(*args, **kwargs)


class UserLogoutEvent(UserEvent):
    def __init__(self, token: str, *args, **kwargs) -> None:
        self.token = token
        super().__init__(*args, **kwargs)
