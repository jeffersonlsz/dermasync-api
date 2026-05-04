"""
Module dispatcher.py.
"""

import logging
from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
    UploadImagesEffect,
    UpdateRelatoStatusEffect,
)
from app.application.effects.handlers import (
    handle_persist_relato,
    handle_enqueue_processing,
    handle_emit_domain_event,
    handle_upload_images,
    handle_update_relato_status,
)
from app.application.effects.idempotency import effect_already_succeeded

logger = logging.getLogger(__name__)

def dispatch_effect(effect, deps: dict) -> bool:
    effect_type = effect.__class__.__name__

    if isinstance(effect, UpdateRelatoStatusEffect):
        effect_ref = effect.new_status.value
    elif isinstance(effect, EmitDomainEventEffect):
        effect_ref = effect.event_name
    else:
        effect_ref = effect.relato_id

    if effect_ref and effect_already_succeeded(
        relato_id=effect.relato_id,
        effect_type=effect_type,
        effect_ref=effect_ref,
    ):
        logger.info(
            "Effect j executado com sucesso | skip | type=%s relato=%s ref=%s",
            effect_type,
            effect.relato_id,
            effect_ref,
        )
        return False # Skipped

    if isinstance(effect, PersistRelatoEffect):
        handle_persist_relato(effect, deps)
    elif isinstance(effect, EnqueueProcessingEffect):
        handle_enqueue_processing(effect, deps)
    elif isinstance(effect, EmitDomainEventEffect):
        handle_emit_domain_event(effect, deps)
    elif isinstance(effect, UploadImagesEffect):
        handle_upload_images(effect, deps)
    elif isinstance(effect, UpdateRelatoStatusEffect):
        handle_update_relato_status(effect, deps)
    else:
        raise ValueError(f"Efeito desconhecido: {effect}")

    return True # Executed
