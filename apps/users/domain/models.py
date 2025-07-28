from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from apps.users.domain.enums import UserType


@dataclass
class User:
    email: str
    password_hash: str | None = field(default=None, repr=False)
    first_name: str = ""
    last_name: str = ""
    phone_number: str = ""
    user_type: UserType = UserType.CLIENT
    is_email_verified: bool = False
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    is_new: bool = True
    id: int | None = None
    uuid: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None
