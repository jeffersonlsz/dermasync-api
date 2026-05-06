# app/domain/relato/effects/rebuild.py

from app.application.effects.result import EffectResult
from app.domain.relato.states import RelatoStatus

from .emit_event import EmitDomainEventEffect
from .enqueue import EnqueueProcessingEffect
from .persist import PersistRelatoEffect
from .rollback import RollbackImagesEffect
from .update_status import UpdateRelatoStatusEffect
from .upload import PersistImageRefsEffect


def rebuild_effect_from_result(result: EffectResult):
    match result.effect_type:
        case "PERSIST_RELATO":
            metadata = result.metadata or {}
            effect_data = metadata.get("effect_data", {})
            status_value = effect_data.get("status") or metadata.get("status")

            return PersistRelatoEffect(
                relato_id=result.relato_id,
                owner_id=effect_data.get("owner_id", ""),
                status=RelatoStatus(status_value) if status_value else None,
                conteudo=effect_data.get("conteudo", ""),
                image_refs=metadata.get("image_refs", {}),
            )

        case "UPLOAD_IMAGES" | "PERSIST_IMAGE_REFS":
            return PersistImageRefsEffect(
                relato_id=result.relato_id,
                image_refs=(result.metadata or {}).get("image_refs", {}),
            )

        case "ENQUEUE_PROCESSING":
            return EnqueueProcessingEffect(relato_id=result.relato_id)

        case "UPDATE_RELATO_STATUS" | "UPDATE_STATUS":
            new_status = (result.metadata or {}).get("new_status")
            return UpdateRelatoStatusEffect(
                relato_id=result.relato_id,
                new_status=RelatoStatus(new_status) if new_status else None,
            )

        case "EMIT_DOMAIN_EVENT" | "EMIT_EVENT":
            metadata = result.metadata or {}
            return EmitDomainEventEffect(
                relato_id=result.relato_id,
                event_name=metadata.get("event_name", ""),
                payload=metadata.get("payload", {}),
            )

        case "ROLLBACK_IMAGES":
            return RollbackImagesEffect(
                image_ids=(result.metadata or {}).get("image_ids", []),
            )

        case _:
            raise ValueError(f"Efeito nao suportado para retry: {result.effect_type}")
