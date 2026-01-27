from datetime import datetime, timezone
from typing import Optional, Dict
import logging

from app.firestore.client import get_firestore_client
from app.domain.relato.states import RelatoStatus

logger = logging.getLogger(__name__)


def persist_relato_firestore(
    *,
    relato_id: str,
    owner_id: str,
    status: RelatoStatus,
    payload: Optional[Dict],
):
    """
    Adapter de persistência real no Firestore.
    NÃO contém regra de negócio.
    """

    db = get_firestore_client()
    now = datetime.now(tz=timezone.utc)

    data = {
        "relato_id": str(relato_id),
        "owner_id": str(owner_id),
        "status": status.value,
        "payload": payload,
        "updated_at": now,
    }

    # Se for criação, adiciona created_at
    if status == RelatoStatus.CREATED:
        data["created_at"] = now

    logger.info(
        "[FIRESTORE] Persistindo relato | id=%s status=%s",
        relato_id,
        status.value,
    )
    
    logger.debug(
        "[FIRESTORE] Dados do relato | id=%s data=%s",
        relato_id,
        data,
    )

    db.collection("relatos").document(relato_id).set(data, merge=True)
