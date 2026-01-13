# tests/domain/ux_effects/test_ux_effect_public_contract.py
import json

from app.domain.ux_effects.processing_started import ProcessingStartedUXEffect
from app.domain.ux_effects.retry import RetryUXEffect
from app.services.ux_serializer import serialize_ux_effects


def test_multiple_ux_effects_preserve_order_and_contract():
    effects = [
        ProcessingStartedUXEffect.default(relato_id="relato_123"),
        RetryUXEffect.retrying(
            relato_id="relato_123",
            count=2,
        ),
    ]

    payload = serialize_ux_effects(effects)

    json.dumps(payload)

    assert payload == {
        "ux_effects": [
            {
                "type": "processing_started",
                "severity": "info",
                "channel": "banner",
                "timing": "after_processing",
                "message": "Seu relato está sendo processado. Isso pode levar alguns instantes.",
            },
            {
                "type": "retrying",
                "severity": "info",
                "channel": "banner",
                "timing": "immediate",
                "message": "2 ações estão sendo repetidas.",
            },
        ]
    }
