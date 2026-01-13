# tests/services/test_ux_effects.py

from app.domain.ux_effects.retry import RetryUXEffect
from app.services.ux_serializer import serialize_ux_effects
from app.domain.ux_effects.processing_started import ProcessingStartedUXEffect


def test_ux_effect_contract_shape():
    effect = RetryUXEffect.none_needed(relato_id="r1")

    data = serialize_ux_effects([effect])[0]

    assert data["type"] == "RetryUXEffect"
    assert data["severity"] in {"info", "warning", "error", "success"}
    assert "channel" in data
    assert "timing" in data




def test_processing_started_ux_effect_contract():
    effect = ProcessingStartedUXEffect.default(relato_id="r1")

    data = serialize_ux_effects([effect])[0]

    assert data["type"] == "ProcessingStartedUXEffect"
    assert data["severity"] == "info"
    assert data["channel"] == "banner"
    assert data["timing"] == "after_processing"
    assert "processado" in data["message"].lower()
