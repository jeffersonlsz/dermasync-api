# app/services/effects/fetch_firestore.py
from typing import List, Optional

import logging

from google.cloud.firestore_v1.base_query import And, FieldFilter

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult, EffectStatus

logger = logging.getLogger(__name__)


def fetch_effect_result_success(
    *,
    relato_id: str,
    effect_type: str,
    effect_ref: str,
) -> Optional[EffectResult]:
    """
    Busca no Firestore um EffectResult com success=True
    para a chave de idempotência fornecida.
    """

    db = get_firestore_client()

    query = (
        db.collection("effect_results")
        .where(
            filter=And(
                [
                    FieldFilter("relato_id", "==", relato_id),
                    FieldFilter("effect_type", "==", effect_type),
                    FieldFilter("metadata.effect_ref", "==", effect_ref),
                    FieldFilter("status", "==", EffectStatus.SUCCESS.value),
                ]
            )
        )
        .limit(1)
    )

    docs = list(query.stream())
    if not docs:
        return None

    data = docs[0].to_dict()
    logger.info(f"Fetched EffectResult success: {data}")

    _metadata = data.get("metadata", {}) or {}
    _metadata["old_executed_at"] = data.get("executed_at")
    if data.get("effect_ref") is not None:
        _metadata["effect_ref"] = data["effect_ref"]

    return EffectResult.success(
        relato_id=data["relato_id"],
        effect_type=data["effect_type"],
        metadata=_metadata,
    )


def fetch_failed_effects(
    *,
    relato_id: str,
) -> List[EffectResult]:
    """
    Busca todos os EffectResults com success=False
    associados a um relato.

    Usado exclusivamente pelo fluxo de retry.
    """

    db = get_firestore_client()

    query = db.collection("effect_results").where(
        filter=And(
            [
                FieldFilter("relato_id", "==", relato_id),
                FieldFilter("status", "in", [EffectStatus.ERROR.value, EffectStatus.RETRYING.value]),
            ]
        )
    )

    results: List[EffectResult] = []

    for doc in query.stream():
        data = doc.to_dict()

        try:
            _metadata = data.get("metadata", {}) or {}
            _metadata["old_executed_at"] = data.get("executed_at")
            if data.get("effect_ref") is not None:
                _metadata["effect_ref"] = data["effect_ref"]
            if data.get("failure_type") is not None:
                _metadata["failure_type"] = data["failure_type"]
            if data.get("retry_decision") is not None:
                _metadata["old_retry_decision"] = data["retry_decision"]

            results.append(EffectResult.error(
                relato_id=data["relato_id"],
                effect_type=data["effect_type"],
                error_message=data.get("error", "Unknown error"),
                metadata=_metadata,
            ))
        except TypeError as exc:
            # Defesa: não quebrar retry por dado legado
            logger.error(
                "EffectResult inválido no Firestore | data=%s | erro=%s",
                data,
                exc,
            )

    logger.info(
        "Fetched %d failed EffectResults for relato=%s",
        len(results),
        relato_id,
    )

    return results
