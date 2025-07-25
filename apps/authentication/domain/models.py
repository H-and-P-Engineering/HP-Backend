from dataclasses import dataclass
from datetime import datetime


@dataclass
class BlackListedToken:
    access: str
    user_id: int
    expires_at: datetime
    id: int | None = None
    created_at: datetime | None = None
