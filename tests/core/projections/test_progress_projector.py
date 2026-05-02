# tests/core/projections/test_progress_projector.py
from datetime import datetime, timedelta

from app.core.projections.progress_projector import (
    UXEffectRecord,
    project_progress,
)


def _effect(
    *,
    relato_id: str,
    type: str,
    subtype: str,
    message: str,
    created_at: datetime,
    channel: str = "progress",
) -> UXEffectRecord:
    return UXEffectRecord(
        effect_id="effect-1",
        relato_id=relato_id,
        type=type,
        subtype=subtype,
        severity="info",
        channel=channel,
        timing="immediate",
        message=message,
        payload=None,
        created_at=created_at,
    )


# =========================
# TEST 1 — NO EFFECTS
# =========================

def test_progress_with_no_effects_all_pending():
    relato_id = "relato-123"

    projection = project_progress(
        relato_id=relato_id,
        effects=[],
    )

    assert projection.progress_pct == 0.0
    assert projection.is_complete is False
    assert projection.has_error is False
    assert projection.summary == "Processando..."

    for step in projection.steps:
        assert step.state == "pending"
        assert step.started_at is None
        assert step.finished_at is None
        assert step.error_message is None


# =========================
# TEST 2 — STARTED + COMPLETED
# =========================

def test_progress_step_completed():
    relato_id = "relato-123"
    t0 = datetime.utcnow()

    effects = [
        _effect(
            relato_id=relato_id,
            type="processing_started",
            subtype="persist_relato",
            message="Persistindo relato...",
            created_at=t0,
        ),
        _effect(
            relato_id=relato_id,
            type="processing_completed",
            subtype="persist_relato",
            message="Relato persistido.",
            created_at=t0 + timedelta(seconds=5),
        ),
    ]

    projection = project_progress(
        relato_id=relato_id,
        effects=effects,
    )

    persist_step = next(
        step for step in projection.steps
        if step.step_id == "persist_relato"
    )

    assert persist_step.state == "done"
    assert persist_step.started_at == t0
    assert persist_step.finished_at == t0 + timedelta(seconds=5)
    assert persist_step.error_message is None

    assert projection.progress_pct > 0.0
    assert projection.has_error is False


# =========================
# TEST 3 — FAILED STEP
# =========================

def test_progress_step_failed_sets_error():
    relato_id = "relato-123"
    t0 = datetime.utcnow()

    effects = [
        _effect(
            relato_id=relato_id,
            type="processing_started",
            subtype="enrich_metadata",
            message="Analisando relato...",
            created_at=t0,
        ),
        _effect(
            relato_id=relato_id,
            type="processing_failed",
            subtype="enrich_metadata",
            message="Falha ao analisar relato.",
            created_at=t0 + timedelta(seconds=10),
        ),
    ]

    projection = project_progress(
        relato_id=relato_id,
        effects=effects,
    )

    enrich_step = next(
        step for step in projection.steps
        if step.step_id == "enrich_metadata"
    )

    assert enrich_step.state == "error"
    assert enrich_step.error_message == "Falha ao analisar relato."

    assert projection.has_error is True
    assert projection.is_complete is False
    assert projection.summary == "Falha ao analisar relato."
