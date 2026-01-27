# tests/ux/test_cognitive_integration_flow.py

from app.domain.ux_effects.processing_started import ProcessingStartedUXEffect
from app.domain.ux_effects.retry import RetryUXEffect
from app.services.ux_serializer import serialize_ux_effects

from tests.ux.ui_interpreter import interpret_for_ui





def test_user_sees_coherent_story_from_ux_effects():
    relato_id = "123"

    effects = [
        ProcessingStartedUXEffect.default(relato_id=relato_id),
        RetryUXEffect.retrying(relato_id=relato_id, count=1),
        RetryUXEffect.retrying(relato_id=relato_id, count=2),
        RetryUXEffect.failed_final(relato_id=relato_id),
    ]

    serialized_effects = serialize_ux_effects(effects)

    ui_story = interpret_for_ui(serialized_effects)

    assert ui_story == [
        "Recebemos seu relato",
        "Tentando novamente...",
        "Tentando novamente...",
        "Não foi possível concluir agora",
    ]
