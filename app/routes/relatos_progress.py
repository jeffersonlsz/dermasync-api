# app/routes/relatos_progress.py
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.progress_snapshot_repository import ProgressSnapshotRepository
from app.services.relato_progress_stabilization_service import (
    RelatoProgressStabilizationService
)

router = APIRouter(
    prefix="/relatos",
    tags=["Relatos - Progress"],
)

import logging
logger = logging.getLogger(__name__)
@router.get(
    "/{relato_id}/progress",
    status_code=status.HTTP_200_OK,
)
def get_relato_progress(
    relato_id: str,
    user: User = Depends(get_current_user),
):
    logger.debug(f"Getting progress for relato_id: {relato_id} by user: {user.id}")
    """
    Retorna o progresso semântico (UXProgress) de um relato.

    Integração:
    - Job de estabilização roda sob demanda
    - Snapshot é usado se estiver estável
    - Domínio continua sendo a fonte semântica
    """

    try:
        logger.debug("Initializing RelatoProgressStabilizationService")
        stabilization_service = RelatoProgressStabilizationService(
            effect_repository=EffectResultRepository(),
            snapshot_repository=ProgressSnapshotRepository(),
        )
        logger.debug("Calling get_or_compute_progress")
        progress_or_snapshot = stabilization_service.get_or_compute_progress(
            relato_id
        )
        logger.debug("Progress computation completed")
    except Exception as exc:
            raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    # --------------------------------------------------------
    # Serialização unificada (UXProgress ou Snapshot)
    # --------------------------------------------------------
    # Snapshot já é estado final → convertemos para formato UX
    # UXProgress segue fluxo normal
    # --------------------------------------------------------

    if hasattr(progress_or_snapshot, "step_states"):
        # É ProgressSnapshot
        return {
            "relato_id": progress_or_snapshot.relato_id,
            "progress_pct": progress_or_snapshot.progress_pct,
            "is_complete": True,
            "has_error": progress_or_snapshot.has_error,
            "summary": "Processo finalizado",
            "updated_at": progress_or_snapshot.updated_at.isoformat(),
            "steps": [
                {
                    "step_id": step_id,
                    "state": state,
                }
                for step_id, state in progress_or_snapshot.step_states.items()
            ],
        }

    # --------------------------------------------------------
    # UXProgress (estado transitório)
    # --------------------------------------------------------
    progress = progress_or_snapshot

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
                "state": step.state.value,
                "weight": step.weight,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "finished_at": step.finished_at.isoformat() if step.finished_at else None,
                "error_message": step.error_message,
            }
            for step in progress.steps
        ],
    }
