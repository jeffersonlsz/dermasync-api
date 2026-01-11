from app.services.effects.result import EffectResult
from app.services.effects.fetch_firestore import fetch_effect_result_success


def effect_already_succeeded(
    *,
    relato_id: str,
    effect_type: str,
    effect_ref: str,
) -> bool:
    """
    Retorna True se já existe um EffectResult success=True
    para a mesma chave de idempotência.
    """
    result: EffectResult | None = fetch_effect_result_success(
        relato_id=relato_id,
        effect_type=effect_type,
        effect_ref=effect_ref,
    )

    return result is not None
