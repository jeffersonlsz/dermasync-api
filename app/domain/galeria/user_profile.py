from dataclasses import dataclass
from enum import Enum
from typing import Optional

class UserRole(Enum):
    USER = "user"
    COLLABORATOR = "collaborator"
    ADMIN = "admin"


class ExposureLevel(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    EXPLORATORY = "exploratory"


@dataclass(frozen=True)
class UserCognitiveProfile:
    user_id: str
    role: UserRole
    relato_base_id: Optional[str]
    exposure_level: ExposureLevel
