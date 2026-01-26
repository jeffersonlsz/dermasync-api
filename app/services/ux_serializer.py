# app/services/ux_serializer.py
from typing import List, Any
from app.services.ux_adapters import domain_effect_to_ux_effect, UXEffect


def serialize_ux_effects(effects: List[Any]) -> List[dict]:
    """
    Adapta uma lista de efeitos de domínio (pré-execução) para UXEffects
    e depois os serializa para um formato de dicionário JSON-friendly.
    """
    # 1. Adaptar de Domain Effect -> UXEffect, ignorando os que não são de UX
    ux_effects: List[UXEffect] = [
        ux
        for effect in effects
        if (ux := domain_effect_to_ux_effect(effect)) is not None
    ]

    # 2. Serializar a lista de UXEffects canônicos para um dicionário simples
    return [
        {
            "type": effect.type,
            "subtype": effect.subtype,
            "severity": effect.severity.value,
            "channel": effect.channel.value,
            "timing": effect.timing.value,
            "message": effect.message,
            "relato_id": effect.relato_id,
        }
        for effect in ux_effects
    ]
