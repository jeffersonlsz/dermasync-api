from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FailureContext:
    """
    Contexto mínimo de falha técnica.
    NÃO depende de EffectResult.
    """

    effect_type: str
    effect_ref: Optional[str]
    error: Optional[str]

