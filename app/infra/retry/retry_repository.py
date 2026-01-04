# app/infra/retry/retry_repository.py
from typing import List
import logging
from datetime import datetime, timedelta

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult
from app.services.effects.retry_decision import RetryDecision

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

    query = db.collection("effect_results").where("success", "==", False)

    if since_minutes is not None:
        since_dt = datetime.utcnow() - timedelta(minutes=since_minutes)
        query = query.where("executed_at", ">=", since_dt)

    query = query.order_by("executed_at").limit(limit)

    docs = query.stream()

    results: List[EffectResult] = []

    for doc in docs:
        data = doc.to_dict()
        if not data:
            continue

        # Defesa extrema: se já foi abortado, ignorar
        retry_decision = data.get("retry_decision")
        if retry_decision and retry_decision.get("should_retry") is False:
            continue

        try:
            result = EffectResult(
                relato_id=data["relato_id"],
                effect_type=data["effect_type"],
                effect_ref=data["effect_ref"],
                success=data["success"],
                failure_type=data.get("failure_type"),
                retry_decision=RetryDecision(**retry_decision)
                if retry_decision
                else None,
                metadata=data.get("metadata"),
                error=data.get("error"),
                executed_at=data["executed_at"],
            )
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
