from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial


@dataclass
class BlackListedToken:
    access: str = field(repr=False)
    user_id: int
    expires_at: datetime
    id: int | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, UTC))
