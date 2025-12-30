import logging
from datetime import datetime

from app.services.effects.result import EffectResult
from app.services.relato_processing_adapter import enqueue_relato_processing

logger = logging.getLogger(__name__)


def execute_enqueue_processing(metadata: dict) -> EffectResult:
    """
    Executor técnico de ENQUEUE_JOB.
    """

    relato_id = metadata["relato_id"]

    try:
        enqueue_relato_processing(relato_id)

        return EffectResult(
            relato_id=relato_id,
            effect_type="ENQUEUE_JOB",
            effect_ref=relato_id,
            success=True,
            metadata=None,
            error=None,
            executed_at=datetime.utcnow(),
        )

    except Exception as exc:
        logger.exception("[ENQUEUE_JOB] Falha ao enfileirar relato")

        return EffectResult(
            relato_id=relato_id,
            effect_type="ENQUEUE_JOB",
            effect_ref=relato_id,
            success=False,
            metadata=None,
            error=str(exc),
            executed_at=datetime.utcnow(),
        )
