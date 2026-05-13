# app/services/ux_adapter_core.py
"""
Mdulo central para adaptar diferentes tipos de efeitos (de domnio, de resultado)
para o contrato cannico de UXEffect.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.application.effects.result import EffectStatus, EffectResult
from app.core.projections.progress_projector import UXEffectRecord
from app.domain.ux_effects.base import UXEffect, UXSeverity, UXChannel, UXTiming

logger = logging.getLogger(__name__)

# =========================================================
# Contrato Cannico do UXEffect
# =========================================================





# =========================================================
# Adapter 1: DomainEffect -> UXEffect
# Para ser usado ANTES da execuo dos efeitos.
# =========================================================

DOMAIN_EFFECT_TO_UX_MAPPING = {
    "PersistRelatoEffect": {
        "subtype": "persist_relato",
        "message": "Relato recebido e salvo.",
    },
    "PersistImageRefsEffect": {
        "subtype": "persist_image_refs",
        "message": "Referencias de imagens associadas ao relato.",
    },
    "EnqueueProcessingEffect": {
        "subtype": "enqueue_processing",
        "message": "Relato na fila para anlise.",
    },
    "UpdateRelatoStatusEffect": {
        "subtype": "update_status",
        "message": "Status do relato atualizado.",
    },
}

def domain_effect_to_ux_effect(effect) -> UXEffect | None:
    """Adapta um efeito de domnio (antes de ser executado) para um UXEffect."""
    effect_name = effect.__class__.__name__
    mapping = DOMAIN_EFFECT_TO_UX_MAPPING.get(effect_name)

    if not mapping:
        logger.debug("Ignoring non-UX domain effect: %s", effect_name)
        return None

    # Efeitos de domnio representam o incio de uma ao
    return UXEffect(
        type="processing_started",
        message=mapping["message"],
        severity=UXSeverity.INFO,
        channel=UXChannel.BANNER,
        timing=UXTiming.IMMEDIATE,
        metadata={
            "subtype": mapping["subtype"],
            "relato_id": getattr(effect, 'relato_id', ''),
        },
    )


# =========================================================
# Adapter 2: EffectResult -> UXEffectRecord
# Movido de 'relatos_progress.py' para centralizao.
# Para ser usado DEPOIS da execuo dos efeitos (com base em resultados persistidos).
# =========================================================

EFFECT_RESULT_TYPE_TO_SUBTYPE = {
    "UPDATE_STATUS": "persist_relato",
    "UPLOAD_IMAGES": "persist_image_refs",
    "PERSIST_IMAGE_REFS": "persist_image_refs",
    "ENQUEUE_PROCESSING": "enqueue_processing",
    "ENRICH_METADATA": "enrich_metadata",
}

def _default_message_for_result(subtype: str) -> str:
    return {
        "persist_relato": "Relato recebido com sucesso.",
        "enqueue_processing": "Relato enviado para processamento.",
        "enrich_metadata": "Anlise do relato concluda.",
    }.get(subtype, "Processamento concludo.")

def effect_result_to_ux_effect(effect: EffectResult, relato_id: str) -> UXEffectRecord | None:

    subtype = EFFECT_RESULT_TYPE_TO_SUBTYPE.get(effect.effect_type)

    if not subtype:
        logger.debug(
            "Ignoring non-UX effect result | type=%s relato=%s",
            effect.effect_type,
            relato_id,
        )
        return None

    if effect.status == EffectStatus.STARTED:
        ux_type = "processing_started"
        severity = UXSeverity.INFO
        message = f"Iniciando {subtype}..."

    elif effect.status == EffectStatus.SUCCESS:
        ux_type = "processing_completed"
        severity = UXSeverity.INFO
        message = _default_message_for_result(subtype)

    elif effect.status == EffectStatus.RETRYING:
        ux_type = "processing_started"
        severity = UXSeverity.WARNING
        message = "Reiniciando processamento..."

    else:
        ux_type = "processing_failed"
        severity = UXSeverity.ERROR
        message = effect.error_message or "Erro no processamento."

    metadata = getattr(effect, "metadata", None)

    return UXEffectRecord(
        effect_id=str(uuid.uuid4()),
        relato_id=relato_id,
        type=ux_type,
        subtype=subtype,
        severity=severity,
        channel=UXChannel.BANNER,
        timing=UXTiming.IMMEDIATE,
        message=message,
        payload=metadata,
        created_at=effect.created_at,
    )
