# app/services/effects/loader.py
from typing import List

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult, EffectStatus


def load_failed_effect_results(
    *,
    limit: int = 100,
) -> List[EffectResult]:
    """
    Carrega EffectResults com falha técnica (success=False).

    NÃO decide retry.
    NÃO executa efeitos.
    NÃO altera estado.
    """

    db = get_firestore_client()

    query = (
        db.collection("effect_results")
        .where("status", "in", [EffectStatus.ERROR.value, EffectStatus.RETRYING.value])
        .order_by("created_at")
        .limit(limit)
    )

    results: List[EffectResult] = []

    for doc in query.stream():
        data = doc.to_dict()

        _metadata = data.get("metadata", {}) or {}
        if "executed_at" in data: # Legacy field
            _metadata["old_executed_at"] = data["executed_at"]
        if "effect_ref" in data: # Legacy field
            _metadata["effect_ref"] = data["effect_ref"]
        if "failure_type" in data:
            _metadata["failure_type"] = data["failure_type"]
        if "retry_decision" in data:
            _metadata["old_retry_decision"] = data["retry_decision"]

        status = EffectStatus(data["status"]) # Convert stored string to enum

        if status == EffectStatus.ERROR:
            results.append(
                EffectResult.error(
                    relato_id=data["relato_id"],
                    effect_type=data["effect_type"],
                    error_message=data.get("error_message", "Unknown error"),
                    metadata=_metadata,
                )
            )
        elif status == EffectStatus.RETRYING:
            results.append(
                EffectResult.retrying(
                    relato_id=data["relato_id"],
                    effect_type=data["effect_type"],
                    retry_after=data.get("retry_after"),
                    metadata=_metadata,
                )
            )

    return results


def load_effect_result(effect_result_id: str) -> EffectResult:
    """
    Carrega um EffectResult específico pelo seu ID de documento.
    """
    db = get_firestore_client()
    doc_ref = db.collection("effect_results").document(effect_result_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise FileNotFoundError(f"EffectResult com ID {effect_result_id} não encontrado.")

    data = doc.to_dict()

    data = doc.to_dict()

    _metadata = data.get("metadata", {}) or {}
    if "executed_at" in data:
        _metadata["old_executed_at"] = data["executed_at"]
    if "effect_ref" in data:
        _metadata["effect_ref"] = data["effect_ref"]
    if "failure_type" in data:
        _metadata["failure_type"] = data["failure_type"]
    if "retry_decision" in data:
        _metadata["old_retry_decision"] = data["retry_decision"]

    status = EffectStatus(data["status"])

    if status == EffectStatus.SUCCESS:
        return EffectResult.success(
            relato_id=data["relato_id"],
            effect_type=data["effect_type"],
            metadata=_metadata,
        )
    elif status == EffectStatus.ERROR:
        return EffectResult.error(
            relato_id=data["relato_id"],
            effect_type=data["effect_type"],
            error_message=data.get("error_message", "Unknown error"),
            metadata=_metadata,
        )
    elif status == EffectStatus.RETRYING:
        return EffectResult.retrying(
            relato_id=data["relato_id"],
            effect_type=data["effect_type"],
            retry_after=data.get("retry_after"),
            metadata=_metadata,
        )
