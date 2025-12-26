from dataclasses import dataclass
from typing import List

from app.domain.relato_status import RelatoStatus
from app.domain.relato_intents import RelatoIntent
from app.domain import relato_guards


@dataclass(frozen=True)
class IntentResult:
    allowed: bool
    reason: str | None
    next_states: List[RelatoStatus]
