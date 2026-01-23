# app/routes/relatos_progress.py
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

from app.repositories.effect_result_repository import EffectResultRepository
from app.core.projections.progress_projector import (
    UXEffectRecord,
    project_progress,
)

import logging
from uuid import uuid4

router = APIRouter(
    prefix="/relatos",
    tags=["Relatos - Progress"],
)

logger = logging.getLogger(__name__)


# =========================================================
# Mapeamento semântico: EffectResult -> Step (subtype)
# =========================================================

EFFECT_TYPE_TO_SUBTYPE = {
    "PERSIST_RELATO": "persist_relato",
    "UPLOAD_IMAGES": "upload_images",
    "ENRICH_METADATA": "enrich_metadata",
    "ENRICH_METADATA_STARTED": "enrich_metadata",
}


def _default_message_for(subtype: str) -> str:
    return {
        "persist_relato": "Relato recebido com sucesso.",
        "upload_images": "Imagens processadas.",
        "enrich_metadata": "Análise do relato concluída.",
    }.get(subtype, "Processamento concluído.")


# =========================================================
# Adapter: EffectResult -> UXEffectRecord
# =========================================================

def effect_result_to_ux_effect(
    effect,
    relato_id: str,
) -> UXEffectRecord:
    subtype = EFFECT_TYPE_TO_SUBTYPE.get(effect.type)

    if not subtype:
        raise ValueError(
            f"Effect type desconhecido: {effect.type}"
        )

    # 🔧 AJUSTE CRÍTICO:
    # Tradução correta do "tipo semântico" do UX Effect
    if effect.type == "ENRICH_METADATA_STARTED":
        ux_type = "processing_started"
    elif effect.success:
        ux_type = "processing_completed"
    else:
        ux_type = "processing_failed"

    # leitura defensiva: metadata pode não existir
    metadata = getattr(effect, "metadata", None)

    return UXEffectRecord(
        effect_id=str(uuid4()),
        relato_id=relato_id,
        type=ux_type,
        subtype=subtype,
        severity="info" if ux_type != "processing_failed" else "error",
        channel="progress",
        timing="immediate",
        message=(
            metadata.get("message")
            if ux_type == "processing_started" and isinstance(metadata, dict)
            else _default_message_for(subtype)
            if ux_type == "processing_completed"
            else effect.error or "Erro no processamento."
        ),
        payload=metadata,
        created_at=effect.executed_at,
    )


# =========================================================
# Endpoint público
# =========================================================

@router.get(
    "/{relato_id}/progress",
    status_code=status.HTTP_200_OK,
)
def get_relato_progress(
    relato_id: str,
    user: User = Depends(get_current_user),
):
    """
    Retorna o progresso semântico de um relato.

    Fonte da verdade:
    - EffectResult persistidos (LEGADO)

    Estratégia:
    - Carrega EffectResult
    - Traduz para UX Effects
    - Projeta progresso
    """

    try:
        logger.debug(
            "Getting progress for relato_id=%s user=%s",
            relato_id,
            user.id,
        )

        effect_repo = EffectResultRepository()

        # 1️⃣ Buscar EffectResult persistidos
        effect_records = effect_repo.fetch_by_relato_id(
            relato_id=relato_id
        )

        logger.debug(
            "Found %d effect records for relato_id=%s",
            len(effect_records),
            relato_id,
        )

        # 2️⃣ Converter para UXEffectRecord (modelo canônico)
        effects = [
            effect_result_to_ux_effect(e, relato_id)
            for e in effect_records
        ]

        # ⚠️ Garantia de ordenação temporal
        effects.sort(key=lambda e: e.created_at)

        # 3️⃣ Projetar progresso
        progress = project_progress(
            relato_id=relato_id,
            effects=effects,
        )

        logger.debug(
            "Projected progress for relato_id=%s",
            relato_id,
        )

    except Exception as exc:
        logger.exception("Error projecting relato progress")
        raise HTTPException(
            status_code=500,
            detail="Erro ao calcular progresso do relato.",
        ) from exc

    # 4️⃣ Serialização explícita (contrato público)
    return {
        "relato_id": progress.relato_id,
        "progress_pct": progress.progress_pct,
        "is_complete": progress.is_complete,
        "has_error": progress.has_error,
        "summary": progress.summary,
        "updated_at": progress.updated_at.isoformat(),
        "steps": [
            {
                "step_id": step.step_id,
                "label": step.label,
                "state": step.state,
                "weight": step.weight,
                "started_at": (
                    step.started_at.isoformat()
                    if step.started_at
                    else None
                ),
                "finished_at": (
                    step.finished_at.isoformat()
                    if step.finished_at
                    else None
                ),
                "error_message": step.error_message,
            }
            for step in progress.steps
        ],
    }
