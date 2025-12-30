# app/services/effects/persist_firestore.py
import logging
import uuid
from datetime import datetime
from typing import Dict

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult

logger = logging.getLogger(__name__)


def persist_effect_result_firestore(
    result: EffectResult,
) -> None:
    """
    Persiste o resultado técnico de execução de um efeito.

    NÃO lança exceção.
    NÃO interfere no fluxo.
    """

    db = get_firestore_client()

    doc_id = uuid.uuid4().hex

    data: Dict = {
        "relato_id": result.relato_id,
        "effect_type": result.effect_type,
        "effect_ref": result.effect_ref,
        "success": result.success,
        "metadata": result.metadata,
        "error": result.error,
        "executed_at": result.executed_at,
        "created_at": datetime.utcnow(),
    }

    try:
        db.collection("effect_results").document(doc_id).set(data)
        logger.debug(
            "[EFFECT_RESULT] Persistido | id=%s type=%s success=%s",
            doc_id,
            result.effect_type,
            result.success,
        )

    except Exception as exc:
        # ⚠️ Nunca quebrar o fluxo principal
        logger.error(
            "[EFFECT_RESULT] Falha ao persistir | type=%s erro=%s",
            result.effect_type,
            exc,
        )
