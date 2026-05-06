from datetime import timedelta

from app.application.effects.result import EffectResult
from app.application.ux.projection import map_effect_result_to_ux


def test_map_effect_result_success_to_ux_effect():
    effect_result = EffectResult.success(
        relato_id="relato-123",
        effect_type="PERSIST_RELATO",
        metadata={"effect_ref": "relato-123"},
    )

    ux_effect = map_effect_result_to_ux(effect_result)

    assert ux_effect.type == "processing_completed"
    assert ux_effect.severity.value == "success"
    assert ux_effect.metadata["subtype"] == "persist_relato"


def test_map_effect_result_retrying_to_ux_effect():
    effect_result = EffectResult.retrying(
        relato_id="relato-123",
        effect_type="ENQUEUE_PROCESSING",
        metadata={"effect_ref": "relato-123"},
        retry_after=timedelta(seconds=30),
    )

    ux_effect = map_effect_result_to_ux(effect_result)

    assert ux_effect.type == "processing_retrying"
    assert ux_effect.severity.value == "warning"
    assert ux_effect.metadata["retry_after_seconds"] == 30.0
