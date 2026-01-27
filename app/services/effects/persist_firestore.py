# app/services/effects/persist_firestore.py
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult, EffectStatus

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
        "relato_id=%s, effect_type=%s, status=%s, "
        "metadata=%s, error_message=%s, created_at=%s, retry_after_seconds=%s",
        result.relato_id,
        result.effect_type,
        result.status.value,
        result.metadata,
        result.error_message,
        result.created_at,
        result.retry_after.total_seconds() if result.retry_after else None,
    )
    data: Dict[str, Any] = {
        "relato_id": result.relato_id,
        "effect_type": result.effect_type,
        "status": result.status.value,
        "metadata": result.metadata,
        "created_at": result.created_at,
    }

    if result.status == EffectStatus.ERROR and result.error_message:
        data["error_message"] = result.error_message
    if result.status == EffectStatus.RETRYING and result.retry_after is not None:
        data["retry_after_seconds"] = result.retry_after.total_seconds()

    try:
        normalized_data = normalize_firestore_value(data)
        logger.debug("[EFFECT_RESULT] app.services.effects.persist_firestore.persist_effect_result_firestore(...) | Persistindo dados normalizados: %s", normalized_data)
        db.collection("effect_results").document(doc_id).set(normalized_data)
        logger.debug(
            "[EFFECT_RESULT] app.services.effects.persist_firestore.persist_effect_result_firestore(...) Persistido | id=%s type=%s success=%s",
            doc_id,
            result.effect_type,
            result.status.value,
        )

    except Exception as exc:
        # ⚠️ Nunca quebrar o fluxo principal
        logger.error(
            "[EFFECT_RESULT] app.services.effects.persist_firestore.persist_effect_result_firestore(...) Falha ao persistir | type=%s erro=%s",
            result.effect_type,
            exc,
            exc_info=True,
        )
