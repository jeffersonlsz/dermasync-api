# app/core/projections/progress_projector.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import logging
logger = logging.getLogger(__name__)



# =========================
# UX EFFECT RECORD (INPUT)
# =========================

@dataclass(frozen=True)
class UXEffectRecord:
    effect_id: str
    relato_id: str
    type: str
    subtype: str
    severity: str
    channel: str
    timing: str
    message: str
    payload: Optional[dict]
    created_at: datetime


# =========================
# PIPELINE DEFINITION
# =========================

PIPELINE_STEPS = [
    {
        "step_id": "persist_relato",
        "label": "Enviando relato para processamento...",
        "weight": 1,
    },
    {
        "step_id": "upload_images",
        "label": "Processando imagens...",
        "weight": 3,
    },
    {
        "step_id": "enrich_metadata",
        "label": "Analisando o relato enviado...",
        "weight": 3,
    },
]


# =========================
# PROJECTION OUTPUT MODELS
# =========================

@dataclass(frozen=True)
class StepProgress:
    step_id: str
    label: str
    state: str  # pending | running | done | error
    weight: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]


@dataclass(frozen=True)
class ProgressProjection:
    relato_id: str
    progress_pct: float
    is_complete: bool
    has_error: bool
    summary: str
    updated_at: datetime
    steps: List[StepProgress]


# =========================
# INTERNAL HELPERS
# =========================

def _infer_step_state(effects: List[UXEffectRecord]) -> str:
    types = {e.type for e in effects}

    if "processing_failed" in types:
        return "error"
    if "processing_completed" in types:
        return "done"
    if "processing_started" in types:
        return "running"

    return "pending"


def _first_started_at(effects: List[UXEffectRecord]) -> Optional[datetime]:
    for e in effects:
        if e.type == "processing_started":
            return e.created_at
    return None


def _finished_at(effects: List[UXEffectRecord]) -> Optional[datetime]:
    for e in effects:
        if e.type in ("processing_completed", "processing_failed"):
            return e.created_at
    return None


def _extract_error_message(effects: List[UXEffectRecord]) -> Optional[str]:
    for e in effects:
        if e.type == "processing_failed":
            return e.message
    return None


def _calculate_progress_pct(steps: List[StepProgress]) -> float:
    total_weight = sum(step.weight for step in steps)
    completed_weight = sum(
        step.weight for step in steps if step.state == "done"
    )

    if total_weight == 0:
        return 0.0

    return completed_weight / total_weight


def _build_summary(effects: List[UXEffectRecord], steps: List[StepProgress]) -> str:
    # Erro tem prioridade narrativa
    for step in steps:
        if step.state == "error" and step.error_message:
            return step.error_message

    # Último effect de progresso
    progress_effects = [
        e for e in effects if e.channel == "progress"
    ]

    if progress_effects:
        return progress_effects[-1].message

    # Fallbacks
    if all(step.state == "done" for step in steps):
        return "Processamento concluído."

    return "Processando..."


# =========================
# PUBLIC PROJECTOR
# =========================

def project_progress(
    relato_id: str,
    effects: List[UXEffectRecord],
) -> ProgressProjection:
    """
    Deterministic projection of UX Effects into progress state.
    This function is PURE and has NO side effects.
    """
    logger.debug(
        "Projecting progress for relato_id=%s with %d effects",
        relato_id,
        len(effects),
    )

    steps_projection: List[StepProgress] = []

    for step_def in PIPELINE_STEPS:
        step_id = step_def["step_id"]

        step_effects = [
            e for e in effects if e.subtype == step_id
        ]

        state = _infer_step_state(step_effects)

        steps_projection.append(
            StepProgress(
                step_id=step_id,
                label=step_def["label"],
                weight=step_def["weight"],
                state=state,
                started_at=_first_started_at(step_effects),
                finished_at=_finished_at(step_effects),
                error_message=_extract_error_message(step_effects),
            )
        )

    progress_pct = _calculate_progress_pct(steps_projection)
    has_error = any(step.state == "error" for step in steps_projection)
    is_complete = all(step.state == "done" for step in steps_projection)

    return ProgressProjection(
        relato_id=relato_id,
        progress_pct=progress_pct,
        is_complete=is_complete,
        has_error=has_error,
        summary=_build_summary(effects, steps_projection),
        updated_at=effects[-1].created_at if effects else datetime.utcnow(),
        steps=steps_projection,
    )
