# app/services/ux_serializer.py
from dataclasses import asdict
from app.domain.ux_effects.base import UXEffect
from typing import List


def serialize_ux_effect(effect: UXEffect) -> dict:
    return {
        "type": effect.__class__.__name__,
        "payload": asdict(effect),
    }


def serialize_ux_effects(effects: list[UXEffect]) -> dict:
    return {
        "ux_effects": [
            {
                "type": effect.type,
                "severity": effect.severity.value,
                "channel": effect.channel.value,
                "timing": effect.timing.value,
                "message": effect.message,
            }
            for effect in effects
        ]
    }

