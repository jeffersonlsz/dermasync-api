# app/services/relato_progress_service.py
from typing import List
from datetime import datetime

from app.domain.ux_progress.progress_aggregator import (
    aggregate_progress,
    EffectResult,
)
from app.domain.ux_progress.step_definition import default_step_definitions


class RelatoProgressService:
    """
    Application Service.

    Responsabilidade:
    - Orquestrar fontes de dados
    - Chamar o domínio
    - NÃO conter regras de domínio
    """

    def __init__(self, effect_repository):
        self.effect_repository = effect_repository

    def get_progress(self, relato_id: str):
        effect_results: List[EffectResult] = (
            self.effect_repository.fetch_by_relato_id(relato_id)
        )

        steps = default_step_definitions()

        return aggregate_progress(
            relato_id=relato_id,
            step_definitions=steps,
            effect_results=effect_results,
        )
