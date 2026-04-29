# app/domain/effects/commands.py
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class EffectCommand:
    """
    Representa uma ORDEM executÃ¡vel emitida pelo domÃ­nio
    ou derivada de um EffectResult para retry.

    NÃƒO Ã© histÃ³rico.
    NÃƒO Ã© resultado.
    Ã‰ intenÃ§Ã£o de execuÃ§Ã£o.
    """

    type: str
    relato_id: str
    effect_ref: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
