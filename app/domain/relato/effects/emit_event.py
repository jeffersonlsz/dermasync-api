# app/domain/relato/effects/emit_event.py
from dataclasses import dataclass
from typing import Optional

from .base import Effect


@dataclass(frozen=True)
class EmitDomainEventEffect(Effect):
    """
    Ordena a emisso de um evento de domnio (log, mtrica, etc).
    """
    relato_id: str
    event_name: str
    payload: Optional[dict] = None
