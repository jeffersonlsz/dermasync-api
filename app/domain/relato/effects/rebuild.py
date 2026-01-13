# app/domain/relato/effects/rebuild.py
from app.services.effects.result import EffectResult
from .persist import PersistRelatoEffect
from .upload import UploadImagesEffect
from .enqueue import EnqueueProcessingEffect
from .update_status import UpdateRelatoStatusEffect
from .emit_event import EmitDomainEventEffect
from .rollback import RollbackImagesEffect


def rebuild_effect_from_result(result: EffectResult):
    match result.effect_type:

        case "PERSIST_RELATO":
            return PersistRelatoEffect(
                relato_id=result.relato_id,
                owner_id=result.metadata.get('owner_id', '') if result.metadata else '',
                status=result.metadata.get('status') if result.metadata else None,
                conteudo=result.metadata.get('conteudo', '') if result.metadata else '',
                imagens=result.metadata.get('imagens', {}) if result.metadata else {},
            )

        case "UPLOAD_IMAGES":
            return UploadImagesEffect(
                relato_id=result.relato_id,
                imagens={},  # imagens já persistidas / metadata futura
            )

        case "ENQUEUE_PROCESSING":
            return EnqueueProcessingEffect(relato_id=result.relato_id)

        case "UPDATE_RELATO_STATUS":
            return UpdateRelatoStatusEffect(
                relato_id=result.relato_id,
                new_status=result.metadata.get('new_status') if result.metadata else None,
            )

        case "EMIT_DOMAIN_EVENT":
            return EmitDomainEventEffect(
                event_name=result.metadata.get('event_name', '') if result.metadata else '',
                payload=result.metadata.get('payload', {}) if result.metadata else {},
            )

        case "ROLLBACK_IMAGES":
            return RollbackImagesEffect(
                image_ids=result.metadata.get('image_ids', []) if result.metadata else [],
            )

        case _:
            raise ValueError(
                f"Efeito não suportado para retry: {result.effect_type}"
            )