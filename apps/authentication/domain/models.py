from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from functools import partial
from typing import List, Tuple
from uuid import UUID

import uuid6


class UserType(StrEnum):
    CLIENT = "CLIENT"
    AGENT = "AGENT"
    VENDOR = "VENDOR"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    ADMIN = "ADMIN"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(tag.value, tag.name) for tag in cls]

    @classmethod
    def values(cls) -> List[str]:
        return [tag.value for tag in cls]


@dataclass
class User:
    email: str
    password_hash: str | None = field(default=None, repr=False)
    first_name: str = ""
    last_name: str = ""
    user_type: UserType = UserType.CLIENT
    is_email_verified: bool = False
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    is_new: bool = False
    id: int | None = None
    uuid: UUID = field(default_factory=uuid6.uuid7)
    created_at: datetime = field(default_factory=partial(datetime.now, UTC))
    updated_at: datetime = field(default_factory=partial(datetime.now, UTC))
    last_login: datetime = field(default_factory=partial(datetime.now, UTC))


@dataclass
class BlackListedToken:
    access: str = field(repr=False)
    user_id: int
    expires_at: datetime
    id: int | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, UTC))
