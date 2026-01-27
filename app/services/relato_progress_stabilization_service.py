# app/services/relato_progress_stabilization_service.py
from datetime import datetime
from typing import Dict

from app.domain.ux_progress.progress_aggregator import aggregate_progress
from app.domain.ux_progress.progress_snapshot import ProgressSnapshot
from app.domain.ux_progress.step_definition import default_step_definitions

from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.progress_snapshot_repository import ProgressSnapshotRepository
from app.services.effects.result import EffectStatus

import logging
logger = logging.getLogger(__name__)

class RelatoProgressStabilizationService:
    """
    Job sob demanda para estabilizar progresso de um relato.

    - Pode ser chamado várias vezes
    - É idempotente
    - Nunca executa effects
    """

    def __init__(
        self,
        effect_repository: EffectResultRepository,
        snapshot_repository: ProgressSnapshotRepository,
    ):
        self.effect_repository = effect_repository
        self.snapshot_repository = snapshot_repository

    def get_or_compute_progress(self, relato_id: str):
        logger.debug(f"Getting or computing progress for relato_id: {relato_id}")
        # --------------------------------------------------
        # 1. Tenta snapshot estável
        # --------------------------------------------------
        snapshot = self.snapshot_repository.get_by_relato_id(relato_id)

        if snapshot and snapshot.is_stable:
            return snapshot  # retorno rápido

        # --------------------------------------------------
        # 2. Lê efeitos
        # --------------------------------------------------
        effect_results = self.effect_repository.fetch_by_relato_id(relato_id)
        logger.debug(f"Fetched {len(effect_results)} effect results for relato_id: {relato_id}")
        # --------------------------------------------------
        # 3. Agrega progresso (domínio)
        # --------------------------------------------------
        step_definitions = default_step_definitions()

        progress = aggregate_progress(
            relato_id=relato_id,
            step_definitions=step_definitions,
            effect_results=effect_results,
        )
        logger.debug(f"Aggregated progress: {progress.progress_pct*100}% for relato_id: {relato_id}")
        # --------------------------------------------------
        # 4. Avalia estabilidade
        # --------------------------------------------------
        is_stable = self._is_progress_stable(
            effect_results=effect_results,
            step_definitions=step_definitions,
        )
        logger.debug(f"Progress stability for relato_id {relato_id}: {is_stable}")
        # --------------------------------------------------
        # 5. Persiste snapshot (se estável)
        # --------------------------------------------------
        if is_stable:
            logger.debug(f"Persisting stable ProgressSnapshot for relato_id: {relato_id}")
            snapshot = ProgressSnapshot(
                relato_id=relato_id,
                progress_pct=progress.progress_pct,
                step_states={
                    step.step_id: step.state.value for step in progress.steps
                },
                has_error=progress.has_error,
                is_stable=True,
                updated_at=datetime.utcnow(),
            )
            from dataclasses import asdict

            logger.debug(f"ProgressSnapshot data to save: {asdict(snapshot)}")
            self.snapshot_repository.save(snapshot)

        return progress

    # ------------------------------------------------------
    # Regra de estabilidade (núcleo conceitual)
    # ------------------------------------------------------
    def _is_progress_stable(
        self,
        effect_results,
        step_definitions,
    ) -> bool:
        """
        Um progresso é estável quando todas as intenções (effects)
        tiveram sucesso no último evento observado.
        """

        last_effect_by_type: Dict[str, bool] = {}

        for effect in effect_results:
            last_effect_by_type[effect.effect_type] = effect.status == EffectStatus.SUCCESS

        for step in step_definitions:
            effect_type = step.completion_effect_type

            if effect_type not in last_effect_by_type:
                return False

            if last_effect_by_type[effect_type] is not True:
                return False

        return True
