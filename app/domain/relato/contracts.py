from dataclasses import dataclass
from typing import Optional
from enum import Enum


# =========================
# Actor
# =========================

class ActorRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ADMIN = "admin"


@dataclass(frozen=True)
class Actor:
    id: str
    role: ActorRole


# =========================
# Context
# =========================

@dataclass(frozen=True)
class RelatoContext:
    relato_id: Optional[str]
    relato_exists: bool
    current_state: Optional["RelatoStatus"]  # forward ref
    owner_id: Optional[str]
    payload: Optional[dict] = None


# =========================
# Guard Result
# =========================

@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reason: Optional[str] = None


# =========================
# Decision
# =========================

@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: Optional[str]
    previous_state: Optional["RelatoStatus"]
    next_state: Optional["RelatoStatus"]
    effects: list
