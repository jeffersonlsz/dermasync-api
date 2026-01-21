# app/services/effects/executors/persist_relato.py
import logging
from datetime import datetime

from app.services.effects.result import EffectResult
from app.services.firestore_relato_adapter import persist_relato_firestore

logger = logging.getLogger(__name__)


def execute_persist_relato(metadata: dict) -> EffectResult:
    """
    Executor técnico de PERSIST_RELATO.
    """

    relato_id = metadata["relato_id"]
    owner_id = metadata["owner_id"]
    payload = metadata["payload"]
    status = metadata["status"]

    try:
        persist_relato_firestore(
            relato_id=relato_id,
            owner_id=owner_id,
            payload=payload,
            status=status,
        )

        return EffectResult(
            relato_id=str(relato_id),
            effect_type="PERSIST_RELATO",
            effect_ref=status.value if hasattr(status, "value") else str(status),
            success=True,
            metadata={
                "status": status.value if hasattr(status, "value") else str(status)
            },
            error=None,
            executed_at=datetime.utcnow(),
        )


    except Exception as exc:
        logger.exception("[PERSIST_RELATO] Falha")

        return EffectResult(
            relato_id=relato_id,
            effect_type="PERSIST_RELATO",
            effect_ref=status,
            success=False,
            metadata={"status": status},
            error=str(exc),
            executed_at=datetime.utcnow(),
        )
