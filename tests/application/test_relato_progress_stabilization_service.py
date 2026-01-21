# app/services/relato_progress_stabilization_service.py
from datetime import datetime
from unittest.mock import Mock

from app.services.relato_progress_stabilization_service import (
    RelatoProgressStabilizationService
)
from app.domain.ux_progress.progress_aggregator import EffectResult


def test_job_returns_snapshot_if_stable_exists():
    snapshot_repo = Mock()
    effect_repo = Mock()

    snapshot_repo.get_by_relato_id.return_value = Mock(is_stable=True)

    service = RelatoProgressStabilizationService(
        effect_repository=effect_repo,
        snapshot_repository=snapshot_repo,
    )

    result = service.get_or_compute_progress("relato_1")

    assert result.is_stable is True
    effect_repo.fetch_by_relato_id.assert_not_called()


def test_job_persists_snapshot_when_progress_is_stable():
    snapshot_repo = Mock()
    effect_repo = Mock()

    snapshot_repo.get_by_relato_id.return_value = None

    effect_repo.fetch_by_relato_id.return_value = [
        EffectResult(
            type="PERSIST_RELATO",
            success=True,
            executed_at=datetime.utcnow(),
        ),
        EffectResult(
            type="UPLOAD_IMAGES",
            success=True,
            executed_at=datetime.utcnow(),
        ),
        EffectResult(
            type="ENRICH_METADATA",
            success=True,
            executed_at=datetime.utcnow(),
        ),
    ]

    service = RelatoProgressStabilizationService(
        effect_repository=effect_repo,
        snapshot_repository=snapshot_repo,
    )

    progress = service.get_or_compute_progress("relato_2")

    snapshot_repo.save.assert_called_once()
    assert progress.progress_pct == 1.0
