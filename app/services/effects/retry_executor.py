# app/services/effects/retry_executor.py

from datetime import datetime

from app.services.effects.result import EffectResult
from app.services.effects.registry import get_effect_executor
from app.services.effects.loader import load_effect_result
from app.services.effects.persist_firestore import persist_effect_result_firestore


def retry_effect(effect_result_id: str) -> EffectResult:
    original = load_effect_result(effect_result_id)

    if original.status == original.status.SUCCESS:
        raise ValueError("EffectResult já foi executado com sucesso")

    effect_ref = original.metadata.get("effect_ref")
    if not effect_ref:
        raise ValueError("Retry requires effect_ref in metadata")

    executor = get_effect_executor(effect_ref)
    if not executor:
        raise ValueError(f"Efeito não suportado para retry: {effect_ref}")

    try:
        executor(original.metadata)

        new_result = EffectResult.success(
            relato_id=original.relato_id,
            effect_type=original.effect_type,
            metadata={
                **original.metadata,
                "retried_at": datetime.utcnow().isoformat(),
            },
        )

    except Exception as exc:
        new_result = EffectResult.error(
            relato_id=original.relato_id,
            effect_type=original.effect_type,
            error_message=str(exc),
            metadata={
                **original.metadata,
                "retried_at": datetime.utcnow().isoformat(),
            },
        )

    persist_effect_result_firestore(new_result)
    return new_result
