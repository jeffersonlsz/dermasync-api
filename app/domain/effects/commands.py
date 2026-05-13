# app/domain/effects/commands.py
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class EffectCommand:
    """
    Representa uma ORDEM executvel emitida pelo domnio
    ou derivada de um EffectResult para retry.

    NÃO  histrico.
    NÃO  resultado.
    É inteno de execuo.
    """

    type: str
    relato_id: str
    effect_ref: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
