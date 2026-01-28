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
    assert payload == [
            {
                "type": "ProcessingStartedUXEffect",
                "severity": "info",
                "channel": "banner",
                "timing": "deferred",
                "message": "Seu relato está sendo processado. Isso pode levar alguns instantes.",
                "metadata": {"relato_id": "relato_123"}
            }
        ]

