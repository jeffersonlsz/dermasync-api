# app/domain/relato/contracts.py
from dataclasses import dataclass, field
from typing import List, Any, Optional
from enum import Enum

from app.domain.relato_status import RelatoStatus

# =========================
# Actor
# =========================
class ActorRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    COLLABORATOR = "colaborador"
    SYSTEM = "system"

@dataclass(frozen=True)
class Actor:
    id: str
    role: ActorRole

# =========================
# Commands
# =========================
@dataclass(frozen=True)
class Command:
    pass

@dataclass(frozen=True)
class CreateRelato(Command):
    relato_id: str
    owner_id: str
    conteudo: str
    imagens: dict

@dataclass(frozen=True)
class SubmitRelato(Command):
    relato_id: str

# =========================
# Decision
# =========================
@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: Optional[str] = None
    effects: List[Any] = field(default_factory=list)
    previous_state: Optional[RelatoStatus] = None
    next_state: Optional[RelatoStatus] = None
