# tests/ux/test_cognitive_integration_flow.py

from app.domain.ux_effects.processing_started import ProcessingStartedUXEffect
from app.domain.ux_effects.retry import RetryUXEffect

from tests.ux.ui_interpreter import interpret_for_ui


def serialize(effect):
    """
    Helper local para simular o serializer público.
    """
    return effect.serialize()


def test_user_sees_coherent_story_from_ux_effects():
    relato_id = "123"

    effects = [
        ProcessingStartedUXEffect.default(relato_id=relato_id),
        RetryUXEffect.retrying(relato_id=relato_id, count=1),
        RetryUXEffect.retrying(relato_id=relato_id, count=2),
        RetryUXEffect.failed_final(relato_id=relato_id),
    ]

    serialized_effects = [e.serialize() for e in effects]

    ui_story = interpret_for_ui(serialized_effects)

    assert ui_story == [
        "Recebemos seu relato",
        "Tentando novamente...",
        "Tentando novamente...",
        "Não foi possível concluir agora",
    ]
