# app/domain/effects/commands.py
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class EffectCommand:
    """
    Representa uma ORDEM executável emitida pelo domínio
    ou derivada de um EffectResult para retry.

    NÃO é histórico.
    NÃO é resultado.
    É intenção de execução.
    """

    type: str
    relato_id: str
    effect_ref: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
