from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from uuid import UUID

import uuid6

from apps.users.domain.enums import UserType


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
