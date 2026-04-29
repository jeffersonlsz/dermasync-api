"""
Module handlers.py.
"""

import logging
from app.domain.relato.effects import (
    PersistRelatoEffect,
    EnqueueProcessingEffect,
    EmitDomainEventEffect,
    UploadImagesEffect,
    UpdateRelatoStatusEffect,
    RollbackImagesEffect,
)
from app.services.effects.audit import record_effect_result

logger = logging.getLogger(__name__)

def handle_persist_relato(effect: PersistRelatoEffect, deps: dict) -> None:
    try:
        deps["persist_relato"](
            relato_id=effect.relato_id,
            owner_id=effect.owner_id,
            status=effect.status.value,
            conteudo=effect.conteudo,
            image_refs=effect.image_refs,
        )
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="PERSIST_RELATO",
            effect_ref=effect.relato_id,
            success=True,
            metadata={
                "status": str(effect.status),
                "effect_data": {
                    "owner_id": str(effect.owner_id),
                    "status": str(effect.status),
                    "conteudo": effect.conteudo,
                },
            }
        )
    except Exception as exc:
        logger.exception("Erro ao persistir relato")
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="PERSIST_RELATO",
            effect_ref=effect.relato_id,
            success=False,
            error=str(exc)
        )
        raise

def handle_enqueue_processing(effect: EnqueueProcessingEffect, deps: dict) -> None:
    try:
        logger.info("Executando EnqueueProcessingEffect | relato=%s", effect.relato_id)
        deps["enqueue_processing"](effect.relato_id)
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="ENQUEUE_PROCESSING",
            effect_ref=effect.relato_id,
            success=True
        )
    except Exception as exc:
        logger.exception("Erro ao enfileirar processamento")
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="ENQUEUE_PROCESSING",
            effect_ref=effect.relato_id,
            success=False,
            error=str(exc)
        )
        raise

def handle_emit_domain_event(effect: EmitDomainEventEffect, deps: dict) -> None:
    relato_id = effect.payload.get("relato_id") if effect.payload else None
    try:
        deps["emit_event"](effect.event_name, effect.payload)
        record_effect_result(
            relato_id=relato_id,
            effect_type="EMIT_EVENT",
            effect_ref=effect.event_name,
            success=True,
            metadata={
                "event_name": effect.event_name,
                "payload_keys": list(effect.payload.keys()) if effect.payload else [],
            }
        )
    except Exception as exc:
        logger.exception("Erro ao emitir evento de domÃ­nio")
        record_effect_result(
            relato_id=relato_id,
            effect_type="EMIT_EVENT",
            effect_ref=effect.event_name,
            success=False,
            error=str(exc)
        )
        raise

def handle_upload_images(effect: UploadImagesEffect, deps: dict) -> None:
    try:
        logger.info("Executando UploadImagesEffect | relato=%s", effect.relato_id)
        uploaded_image_ids = deps["upload_images"](
            effect.relato_id,
            effect.image_refs,
        )
        total_imgs = sum(len(v) if v else 0 for v in effect.image_refs.values())
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="UPLOAD_IMAGES",
            effect_ref=effect.relato_id,
            success=True,
            metadata={
                "total_images": total_imgs,
                "image_ids": uploaded_image_ids,
            }
        )
    except Exception as exc:
        logger.exception("Erro no upload de imagens")
        if deps.get("rollback_images") is not None:
            try:
                logger.info("Executando rollback de imagens | relato=%s", effect.relato_id)
                deps["rollback_images"]([])
            except Exception:
                logger.exception("Falha ao executar rollback de imagens | relato=%s", effect.relato_id)
        
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="UPLOAD_IMAGES",
            effect_ref=effect.relato_id,
            success=False,
            error=str(exc)
        )
        raise

def handle_update_relato_status(effect: UpdateRelatoStatusEffect, deps: dict) -> None:
    try:
        deps["update_relato_status"](effect.relato_id, effect.new_status)
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="UPDATE_STATUS",
            effect_ref=effect.new_status.value,
            success=True,
            metadata={"new_status": effect.new_status.value}
        )
    except Exception as exc:
        logger.exception("Erro ao atualizar status do relato")
        record_effect_result(
            relato_id=effect.relato_id,
            effect_type="UPDATE_STATUS",
            effect_ref=effect.new_status.value,
            success=False,
            error=str(exc),
            metadata={"new_status": effect.new_status.value}
        )
        raise

def handle_rollback_compensatory(executed_effects: list, deps: dict) -> None:
    for executed in reversed(executed_effects):
        if isinstance(executed, UploadImagesEffect):
            try:
                image_ids = []
                rollback = RollbackImagesEffect(image_ids=image_ids)
                logger.info("Executando RollbackImagesEffect | imagens=%s", rollback.image_ids)
                if deps.get("rollback_images") is not None:
                    deps["rollback_images"](rollback.image_ids)
            except Exception:
                logger.exception("Falha durante rollback de imagens | relato=%s", getattr(executed, "relato_id", None))
