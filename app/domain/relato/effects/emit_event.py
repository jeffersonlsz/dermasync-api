# app/domain/relato/effects/emit_event.py
from dataclasses import dataclass
from typing import Optional

from .base import Effect


@dataclass(frozen=True)
class EmitDomainEventEffect(Effect):
    """
    Ordena a emissão de um evento de domínio (log, métrica, etc).
    """
    event_name: str
    payload: Optional[dict] = None