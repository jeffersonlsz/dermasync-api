import logging
from datetime import datetime

from app.services.effects.result import EffectResult

logger = logging.getLogger(__name__)


def execute_emit_domain_event(metadata: dict) -> EffectResult:
    """
    Executor técnico de EMIT_DOMAIN_EVENT.
    """

    relato_id = metadata["relato_id"]
    event_name = metadata["event_name"]
    payload = metadata.get("payload")

    try:
        # Por enquanto: apenas log estruturado
        # No futuro: Pub/Sub, EventBridge, Kafka, etc
        logger.info(
            "[DOMAIN_EVENT] %s | relato=%s payload=%s",
            event_name,
            relato_id,
            payload,
        )

        return EffectResult.success(
            relato_id=relato_id,
            effect_type="EMIT_DOMAIN_EVENT",
            metadata={
                "payload": payload,
                "effect_ref": event_name,
            },
        )

    except Exception as exc:
        logger.exception("[EMIT_DOMAIN_EVENT] Falha")

        return EffectResult.error(
            relato_id=relato_id,
            effect_type="EMIT_DOMAIN_EVENT",
            error_message=str(exc),
            metadata={
                "payload": payload,
                "effect_ref": event_name,
            },
        )
