from enum import StrEnum
from typing import List, Tuple


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    SUCCESSFUL = "SUCCESSFUL"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(member.value, member.name) for member in cls]

    @classmethod
    def values(cls) -> List[str]:
        return [member.value for member in cls]
