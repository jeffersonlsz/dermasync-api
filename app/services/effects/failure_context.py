# app/services/effects/failure_context.py
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FailureContext:
    """
    Contexto mÃ­nimo de falha tÃ©cnica.
    NÃƒO depende de EffectResult.
    """

    effect_type: str
    effect_ref: Optional[str]
    error: Optional[str]

