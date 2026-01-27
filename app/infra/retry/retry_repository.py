# app/infra/retry/retry_repository.py
from typing import List
import logging
from datetime import datetime, timedelta

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult, EffectStatus


logger = logging.getLogger(__name__)


def load_failed_effect_results(
    *,
    since_minutes: int | None = None,
    limit: int = 100,
) -> List[EffectResult]:
    """
    Carrega EffectResults falhos e elegíveis para retry.
    NÃO decide retry.
    """

    db = get_firestore_client()
    if not db:
        raise RuntimeError("Firestore client indisponível")

    query = db.collection("effect_results").where("status", "in", [EffectStatus.ERROR.value, EffectStatus.RETRYING.value])

    if since_minutes is not None:
        since_dt = datetime.utcnow() - timedelta(minutes=since_minutes)
        query = query.where("created_at", ">=", since_dt)

    query = query.order_by("created_at").limit(limit)

    docs = query.stream()

    results: List[EffectResult] = []

    for doc in docs:
        data = doc.to_dict()
        if not data:
            continue

        try:
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

            if status == EffectStatus.ERROR:
                result = EffectResult.error(
                    relato_id=data["relato_id"],
                    effect_type=data["effect_type"],
                    error_message=data.get("error_message", data.get("error", "Unknown error")),
                    metadata=_metadata,
                )
            elif status == EffectStatus.RETRYING:
                retry_after_seconds = data.get("retry_after_seconds")
                retry_after_timedelta = timedelta(seconds=retry_after_seconds) if retry_after_seconds is not None else None
                result = EffectResult.retrying(
                    relato_id=data["relato_id"],
                    effect_type=data["effect_type"],
                    retry_after=retry_after_timedelta,
                    metadata=_metadata,
                )
            else:
                # Should not happen due to query filter, but as a safeguard
                logger.warning(
                    "Unexpected EffectResult status '%s' encountered in retry repository for doc_id=%s",
                    status.value, doc.id
                )
                continue

            results.append(result)

        except Exception as exc:
            logger.exception(
                "Falha ao materializar EffectResult | doc_id=%s", doc.id
            )

    logger.info(
        "RetryRepository | carregados=%d | limit=%d",
        len(results),
        limit,
    )

    return results
