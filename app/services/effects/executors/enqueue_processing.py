# app/services/effects/executors/enqueue_processing.py
import logging
from datetime import datetime

from app.services.effects.result import EffectResult
from app.services.relato_processing_adapter import enqueue_relato_processing

logger = logging.getLogger(__name__)


def execute_enqueue_processing(relato_id: str) -> EffectResult:
    """
    Executor técnico do EnqueueProcessingEffect.

    Responsabilidade:
    - Disparar processamento assíncrono
    - NÃO executar jobs
    - NÃO decidir quais jobs existem
    """

    try:
        enqueue_relato_processing(relato_id)

        return EffectResult(
            relato_id=relato_id,
            effect_type="ENQUEUE_PROCESSING",
            effect_ref=relato_id,
            success=True,
            metadata=None,
            error=None,
            executed_at=datetime.utcnow(),
        )

    except Exception as exc:
        logger.exception("[ENQUEUE_PROCESSING] Falha ao enfileirar relato")

        return EffectResult(
            relato_id=relato_id,
            effect_type="ENQUEUE_PROCESSING",
            effect_ref=relato_id,
            success=False,
            metadata=None,
            error=str(exc),
            executed_at=datetime.utcnow(),
        )
