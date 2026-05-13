from typing import Iterable, List

from app.application.effects.result import EffectResult, EffectStatus
from app.domain.ux_effects.base import UXChannel, UXEffect, UXSeverity, UXTiming


EFFECT_RESULT_TYPE_TO_SUBTYPE = {
    "PERSIST_RELATO": "persist_relato",
    "PERSIST_IMAGE_REFS": "persist_image_refs",
    "UPLOAD_IMAGES": "persist_image_refs",
    "UPDATE_STATUS": "update_status",
    "ENQUEUE_PROCESSING": "enqueue_processing",
    "EMIT_EVENT": "emit_event",
    "ENRICH_METADATA": "enrich_metadata",
}


def _subtype_for(effect_result: EffectResult) -> str:
    return EFFECT_RESULT_TYPE_TO_SUBTYPE.get(
        effect_result.effect_type,
        effect_result.effect_type.lower(),
    )


def _message_for(effect_result: EffectResult, subtype: str) -> str:
    if effect_result.status == EffectStatus.SUCCESS:
        messages = {
            "persist_relato": "Relato recebido com sucesso.",
            "persist_image_refs": "Referencias de imagens associadas com sucesso.",
            "update_status": "Status do relato atualizado.",
            "enqueue_processing": "Relato enviado para processamento.",
            "emit_event": "Evento do relato registrado.",
            "enrich_metadata": "Analise do relato concluida.",
        }
        return messages.get(subtype, "Processamento concluido.")

    if effect_result.status == EffectStatus.RETRYING:
        return "Processamento sera tentado novamente."

    if effect_result.status == EffectStatus.STARTED:
        return "Processamento iniciado."

    return effect_result.error_message or "Erro no processamento."


def map_effect_result_to_ux(effect_result: EffectResult) -> UXEffect:
    subtype = _subtype_for(effect_result)

    if effect_result.status == EffectStatus.SUCCESS:
        ux_type = "processing_completed"
        severity = UXSeverity.SUCCESS
        timing = UXTiming.IMMEDIATE
    elif effect_result.status == EffectStatus.RETRYING:
        ux_type = "processing_retrying"
        severity = UXSeverity.WARNING
        timing = UXTiming.DEFERRED
    elif effect_result.status == EffectStatus.STARTED:
        ux_type = "processing_started"
        severity = UXSeverity.INFO
        timing = UXTiming.IMMEDIATE
    else:
        ux_type = "processing_failed"
        severity = UXSeverity.ERROR
        timing = UXTiming.IMMEDIATE

    metadata = {
        "relato_id": effect_result.relato_id,
        "effect_type": effect_result.effect_type,
        "subtype": subtype,
        **(effect_result.metadata or {}),
    }

    if effect_result.retry_after is not None:
        metadata["retry_after_seconds"] = effect_result.retry_after.total_seconds()

    return UXEffect(
        type=ux_type,
        message=_message_for(effect_result, subtype),
        severity=severity,
        channel=UXChannel.BANNER,
        timing=timing,
        metadata=metadata,
    )


def map_effect_results_to_ux(effect_results: Iterable[EffectResult]) -> List[UXEffect]:
    return [map_effect_result_to_ux(effect_result) for effect_result in effect_results]
