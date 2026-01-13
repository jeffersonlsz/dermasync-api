# tests/domain/ux_effects/test_ux_effect_public_contract.py
import json

from app.domain.ux_effects.processing_started import ProcessingStartedUXEffect
from app.services.ux_serializer import serialize_ux_effects


def test_ux_effect_public_contract_snapshot():
    """
    Este teste protege o CONTRATO PÚBLICO de UX Effects.
    Qualquer alteração aqui é BREAKING CHANGE.
    """

    effect = ProcessingStartedUXEffect.default(
        relato_id="relato_123"
    )

    payload = serialize_ux_effects([effect])

    # Garantia 1: serializável em JSON puro
    json.dumps(payload)

    # Garantia 2: shape público estável
    assert payload == {
        "ux_effects": [
            {
                "type": "processing_started",
                "severity": "info",
                "channel": "banner",
                "timing": "after_processing",
                "message": "Seu relato está sendo processado. Isso pode levar alguns instantes.",
            }
        ]
    }

