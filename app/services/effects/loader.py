# app/services/effects/loader.py
from typing import List

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult


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
        .where("success", "==", False)
        .order_by("executed_at")
        .limit(limit)
    )

    results: List[EffectResult] = []

    for doc in query.stream():
        data = doc.to_dict()

        results.append(
            EffectResult(
                relato_id=data["relato_id"],
                effect_type=data["effect_type"],
                effect_ref=data["effect_ref"],
                success=data["success"],
                metadata=data.get("metadata"),
                error=data.get("error"),
                executed_at=data["executed_at"],
            )
        )

    return results
