# app/routes/relatos_progress.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

from app.repositories.effect_result_repository import EffectResultRepository
from app.core.projections.progress_projector import project_progress
from app.services.ux_adapters import effect_result_to_ux_effect


router = APIRouter(
    prefix="/relatos",
    tags=["Relatos - Progress"],
)

logger = logging.getLogger(__name__)


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
    - Traduz para UX Effects (via adapter centralizado)
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

        # 2️⃣ Converter para UXEffectRecord (modelo canônico via adapter)
        effects = [
            ux
            for e in effect_records
            if (ux := effect_result_to_ux_effect(e, relato_id)) is not None
        ]

        logger.debug(
            "Converted effect records to UXEffectRecords for relato_id=%s",
            relato_id,
        )
        # ⚠️ Garantia de ordenação temporal
        effects.sort(key=lambda e: e.created_at)
        logger.debug(
            "Sorted UXEffectRecords for relato_id=%s",
            relato_id,
        )
        # 3️⃣ Projetar progresso
        progress = project_progress(
            relato_id=relato_id,
            effects=effects,
        )

        logger.debug(
            "Projected progress for relato_id=%s",
            relato_id,
        )

    except HTTPException as he:
        raise he
    except Exception as exc:
        logger.exception("Error projecting relato progress")
        raise HTTPException(
            status_code=500,
            detail="Erro ao calcular progresso do relato.",
        ) from exc

    # 4️⃣ Serialização explícita (contrato público)
    return {
        "relato_id": progress.relato_id,
        "progress_pct": progress.progress_pct * 100, # Multiplied by 100
        "is_complete": progress.is_complete,
        "has_error": progress.has_error,
        "failed": 1 if progress.has_error else 0, # Added this line
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