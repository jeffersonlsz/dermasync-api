# app/firestore/persistencia.py

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from app.firestore.client import get_firestore_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def salvar_relato_firestore(
    *,
    relato_id: str,
    owner_id: str,
    payload: Dict[str, Any],
    status: str,
    collection: str = "relatos",
) -> str:
    """
    Persiste o relato no Firestore seguindo o contrato canônico do domínio.

    Este método é:
    - idempotente (set por ID)
    - explícito (sem dict genérico)
    - alinhado com FSM / Orchestrator

    Retorna o relato_id persistido.
    """

    logger.info(
        "[PERSIST] Salvando relato %s na coleção '%s'",
        relato_id,
        collection,
    )

    db = get_firestore_client()

    doc = {
        "id": relato_id,
        "owner_id": owner_id,
        "payload": payload,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection(collection).document(relato_id).set(doc)

    logger.info("[PERSIST] Relato salvo com sucesso: %s", relato_id)

    return relato_id
