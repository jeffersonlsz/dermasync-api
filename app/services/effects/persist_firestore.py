# app/services/effects/persist_firestore.py
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult

logger = logging.getLogger(__name__)


def normalize_firestore_value(value: Any) -> Any:
    """
    Normaliza recursivamente valores para serem compatíveis com o Firestore.
    Converte UUIDs para strings e percorre dicts e lists.
    """
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: normalize_firestore_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_firestore_value(v) for v in value]
    # Mantém outros tipos primitivos (str, int, bool, None, datetime)
    return value


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
    logger.debug(
        "[EFFECT_RESULT] Persistindo EffectResult | "
        "relato_id=%s, effect_type=%s, effect_ref=%s, success=%s, "
        "failure_type=%s, retry_decision=%s, metadata=%s, error=%s, "
        "executed_at=%s, created_at=%s",
        result.relato_id,
        result.effect_type,
        result.effect_ref,
        result.success,
        result.failure_type,
        result.retry_decision,
        result.metadata,
        result.error,
        result.executed_at,
        result.created_at,
    )
    data: Dict[str, Any] = {
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
        normalized_data = normalize_firestore_value(data)
        logger.debug("[EFFECT_RESULT] app.services.effects.persist_firestore.persist_effect_result_firestore(...) | Persistindo dados normalizados: %s", normalized_data)
        db.collection("effect_results").document(doc_id).set(normalized_data)
        logger.debug(
            "[EFFECT_RESULT] app.services.effects.persist_firestore.persist_effect_result_firestore(...) Persistido | id=%s type=%s success=%s",
            doc_id,
            result.effect_type,
            result.success,
        )

    except Exception as exc:
        # ⚠️ Nunca quebrar o fluxo principal
        logger.error(
            "[EFFECT_RESULT] app.services.effects.persist_firestore.persist_effect_result_firestore(...) Falha ao persistir | type=%s erro=%s",
            result.effect_type,
            exc,
            exc_info=True,
        )
