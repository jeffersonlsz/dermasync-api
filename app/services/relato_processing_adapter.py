from datetime import datetime, timezone
import logging

from app.firestore.client import get_firestore_client

logger = logging.getLogger(__name__)


def enqueue_relato_processing(relato_id: str):
    """
    Adapter de enfileiramento de processamento.
    NÃO executa pipeline.
    """

    db = get_firestore_client()
    now = datetime.now(tz=timezone.utc)

    job = {
        "relato_id": str(relato_id),
        "status": "queued",
        "created_at": now,
    }

    logger.info(
        "[QUEUE] Relato enfileirado para processamento | id=%s",
        relato_id,
    )

    db.collection("relato_jobs").document(relato_id).set(job)
