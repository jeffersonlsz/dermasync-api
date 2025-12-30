from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.services.effects.retry_classifier import RetryFailureType
from app.services.effects.retry_decision import RetryDecision


@dataclass(frozen=True)
class EffectResult:
    """
    Resultado técnico da execução de um efeito.

    NÃO representa estado de domínio.
    NÃO governa fluxo.
    NÃO decide retry.
    """

    relato_id: str
    effect_type: str
    effect_ref: str
    success: bool

    # ---- retry / falha (opcionais)
    failure_type: Optional[RetryFailureType] = None
    retry_decision: Optional[RetryDecision] = None

    # ---- técnicos
    metadata: Optional[dict] = None
    error: Optional[str] = None

    executed_at: datetime = datetime.utcnow()
