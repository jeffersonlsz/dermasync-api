from app.services.effects.registry import get_effect_executor, clear_registry
from app.services.effects.register_effects import register_all_effect_executors


def test_all_effects_registered():
    clear_registry()
    register_all_effect_executors()

    assert get_effect_executor("UPLOAD_IMAGE") is not None
    assert get_effect_executor("ENQUEUE_JOB") is not None
    assert get_effect_executor("EMIT_DOMAIN_EVENT") is not None
    assert get_effect_executor("PERSIST_RELATO") is not None
