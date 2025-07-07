from enum import StrEnum
from typing import List, Tuple


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
