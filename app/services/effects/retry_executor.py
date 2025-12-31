# app/services/effects/retry_engine.py

from datetime import datetime

from app.services.effects.result import EffectResult
from app.services.effects.registry import get_effect_executor
from app.services.effects.loader import load_effect_result
from app.services.effects.persist_firestore import persist_effect_result_firestore


def retry_effect(effect_result_id: str) -> EffectResult:
    original = load_effect_result(effect_result_id)

    if original.success:
        raise ValueError("EffectResult já foi executado com sucesso")

    executor = get_effect_executor(original.effect_type)
    if not executor:
        raise ValueError(
            f"Efeito não suportado para retry: {original.effect_type}"
        )

    try:
        executor(original.metadata)

        new_result = EffectResult(
            relato_id=original.relato_id,
            effect_type=original.effect_type,
            effect_ref=original.effect_ref,
            success=True,
            metadata=original.metadata,
            error=None,
            executed_at=datetime.utcnow(),
        )

    except Exception as exc:
        new_result = EffectResult(
            relato_id=original.relato_id,
            effect_type=original.effect_type,
            effect_ref=original.effect_ref,
            success=False,
            metadata=original.metadata,
            error=str(exc),
            executed_at=datetime.utcnow(),
        )

    persist_effect_result_firestore(new_result)
    return new_result
