from typing import Any, Dict

from app.core.events import DomainEvent


class UserEvent(DomainEvent):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id


class UserUpdateEvent(UserEvent):
    def __init__(self, user_id: int, **kwargs) -> None:
        super().__init__(user_id)
        self.update_fields = {**kwargs}
