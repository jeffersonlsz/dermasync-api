"""
Module retry_service.py.
"""

import logging
from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
)
from app.services.effects.result import EffectResult
from app.core.errors import RetryErrorMessages

logger = logging.getLogger(__name__)

def build_effect_from_result(effect_result: EffectResult):
    effect_type = effect_result.effect_type
    relato_id = effect_result.relato_id

    if effect_type == "PERSIST_RELATO":
        effect_data = effect_result.metadata.get("effect_data", {})
        return PersistRelatoEffect(relato_id=relato_id, **effect_data)

    elif effect_type == "ENQUEUE_PROCESSING":
        return EnqueueProcessingEffect(relato_id=relato_id)

    elif effect_type == "EMIT_EVENT":
        return EmitDomainEventEffect(
            event_name=effect_result.metadata.get("effect_ref"),
            payload=effect_result.metadata.get("payload") if effect_result.metadata else None,
            relato_id=relato_id,
        )

    elif effect_type == "UPLOAD_IMAGES":
        raise ValueError(RetryErrorMessages.UPLOAD_IMAGES_NOT_SUPPORTED.value)
    else:
        raise ValueError(f"Retry nÃ£o suportado para effect_type={effect_type}")

def execute_retry(executor, effect_result: EffectResult, attempt: int):
    effect_type = effect_result.effect_type
    relato_id = effect_result.relato_id

    logger.info(
        "RetryExecutor | effect=%s | relato=%s | attempt=%d",
        effect_type,
        relato_id,
        attempt,
    )

    effect = build_effect_from_result(effect_result)

    try:
        executor.execute([effect])
    except Exception as exc:
        logger.exception(
            "RetryExecutor | falha ao reexecutar effect=%s | relato=%s",
            effect_type,
            relato_id,
        )
        raise exc
