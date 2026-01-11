# app/services/effects/fetch_firestore.py

from typing import Optional

from app.firestore.client import get_firestore_client
from app.services.effects.result import EffectResult

import logging
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

    Retorna:
    - EffectResult se encontrado
    - None caso contrário
    """

    db = get_firestore_client()

    query = (
        db.collection("effect_results")
        .where("relato_id", "==", relato_id)
        .where("effect_type", "==", effect_type)
        .where("effect_ref", "==", effect_ref)
        .where("success", "==", True)
        .limit(1)
    )

    docs = list(query.stream())

    if not docs:
        return None

    doc = docs[0]
    data = doc.to_dict()
    logger.info(
        f"Fetched EffectResult from Firestore: {data}"
    )
    # Reconstrói EffectResult a partir do Firestore
    return EffectResult(**data)
