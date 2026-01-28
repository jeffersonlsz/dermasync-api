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

    assert payload == [
            {
                "type": "ProcessingStartedUXEffect",
                "severity": "info",
                "channel": "banner",
                "timing": "deferred",
                "message": "Seu relato está sendo processado. Isso pode levar alguns instantes.",
                "metadata": {"relato_id": "relato_123"}
            },
            {
                "type": "RetryUXEffect",
                "severity": "info",
                "channel": "banner",
                "timing": "immediate",
                "message": "2 ações estão sendo repetidas.",
                "metadata": {"relato_id": "relato_123"},
                "failed_effects_count": 2
            },
        ]
