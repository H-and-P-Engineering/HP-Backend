from enum import Enum
from typing import List, Tuple


class UserType(Enum):
    CLIENT = "CLIENT"
    AGENT = "AGENT"
    VENDOR = "VENDOR"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    ADMIN = "ADMIN"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(member.value, member.name) for member in cls]

    @classmethod
    def values(cls) -> List[str]:
        return [member.value for member in cls]
