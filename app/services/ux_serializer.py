# app/services/ux_serializer.py
from typing import List, Any
from app.services.ux_adapters import domain_effect_to_ux_effect, UXEffect


def serialize_ux_effects(effects: List[Any]) -> List[dict]:
    """
    Serializa uma lista de efeitos (DomainEffect ou UXEffect)
    para um formato de dicionário JSON-friendly.
    """
    serialized_list = []
    for effect in effects:
        if isinstance(effect, UXEffect):
            # If it's already a UXEffect, serialize it directly
            serialized_item = {
                "type": effect.type,
                "message": effect.message,
                "severity": effect.severity.value,
                "channel": effect.channel.value,
                "timing": effect.timing.value,
                "metadata": effect.metadata,
            }
            if hasattr(effect, "failed_effects_count"):
                serialized_item["failed_effects_count"] = effect.failed_effects_count
            serialized_list.append(serialized_item)
        else:
            # Otherwise, try to adapt from DomainEffect
            ux = domain_effect_to_ux_effect(effect)
            if ux is not None:
                serialized_list.append({
                    "type": ux.type,
                    "message": ux.message,
                    "severity": ux.severity.value,
                    "channel": ux.channel.value,
                    "timing": ux.timing.value,
                    "metadata": ux.metadata,
                })
    return serialized_list
