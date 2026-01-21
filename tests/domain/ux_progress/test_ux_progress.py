# tests/domain/ux_progress/test_ux_progress.py
from app.domain.ux_progress.progress_aggregator import StepState, aggregate_progress, find_step
from app.services.effects.result import EffectResult
from app.domain.ux_progress.step_definition import default_step_definitions


def test_progress_with_no_effects_returns_all_steps_pending():
    steps = default_step_definitions()

    progress = aggregate_progress(
        relato_id="r1",
        step_definitions=steps,
        effect_results=[]
    )

    assert progress.progress_pct == 0
    assert progress.is_complete is False
    assert progress.has_error is False

    for step in progress.steps:
        assert step.state == StepState.PENDING


def test_persist_relato_marks_first_step_done():
    steps = default_step_definitions()

    effects = [
        EffectResult(
            type="PERSIST_RELATO",
            success=True,
            executed_at=dt("2026-01-17T10:00:00")
        )
    ]

    progress = aggregate_progress("r1", steps, effects)

    step1 = progress.steps[0]

    assert step1.state == StepState.DONE
    assert progress.progress_pct > 0
    assert progress.summary == step1.label

def test_upload_images_becomes_active_when_effect_exists_but_not_completed():
    steps = default_step_definitions()

    effects = [
        EffectResult(type="PERSIST_RELATO", success=True),
        EffectResult(type="UPLOAD_IMAGES", success=False)
    ]

    progress = aggregate_progress("r1", steps, effects)

    upload_step = find_step(progress, "upload_images")

    assert upload_step.state == StepState.ACTIVE
    assert progress.is_complete is False

def test_upload_images_has_more_weight_in_progress():
    steps = default_step_definitions()

    effects = [
        EffectResult(type="PERSIST_RELATO", success=True),
        EffectResult(type="UPLOAD_IMAGES", success=True),
    ]

    progress = aggregate_progress("r1", steps, effects)

    assert progress.progress_pct > 0.5

def test_error_in_any_step_sets_has_error():
    steps = default_step_definitions()

    effects = [
        EffectResult(type="PERSIST_RELATO", success=True),
        EffectResult(type="UPLOAD_IMAGES", success=False),
    ]

    progress = aggregate_progress("r1", steps, effects)

    assert progress.has_error is True
    assert progress.is_complete is False

def test_all_steps_done_marks_progress_complete():
    steps = default_step_definitions()

    effects = [
        EffectResult(type="PERSIST_RELATO", success=True),
        EffectResult(type="UPLOAD_IMAGES", success=True),
        EffectResult(type="ENRICH_METADATA", success=True),
    ]

    progress = aggregate_progress("r1", steps, effects)

    assert progress.is_complete is True
    assert progress.progress_pct == 1.0
