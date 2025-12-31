# app/infra/retry/retry_scheduler.py

import logging
from typing import Iterable, List

from app.services.effects.result import EffectResult
from app.services.effects.retry_decision import RetryDecision
from app.services.effects.retry_engine import RetryEngine  # engine de decisão
from app.services.effects.loader import load_failed_effect_results


logger = logging.getLogger(__name__)


class RetryScheduler:
    """
    Scheduler técnico de retry (job periódico).

    - NÃO executa efeitos
    - NÃO decide política
    - NÃO altera domínio
    - Apenas observa falhas e agenda decisões
    """

    def __init__(self, *, engine: RetryEngine):
        self._engine = engine

    def run(self) -> List[RetryDecision]:
        """
        Executa um ciclo de avaliação de retries.

        Retorna decisões tomadas (para observabilidade/testes).
        """
        failed_results = self._load_candidates()
        decisions: List[RetryDecision] = []

        for result in failed_results:
            decision = self._engine.decide(result)
            decisions.append(decision)

            self._log_decision(result, decision)

            # ⚠️ Execução futura (NÃO IMPLEMENTAR AGORA)
            # if decision.should_retry:
            #     enqueue_retry(result, decision)

        return decisions

    def _load_candidates(self) -> Iterable[EffectResult]:
        """
        Carrega EffectResults elegíveis para retry.
        """
        return load_failed_effect_results()

    @staticmethod
    def _log_decision(
        result: EffectResult,
        decision: RetryDecision,
    ) -> None:
        logger.info(
            "[RETRY_SCHEDULER] effect=%s ref=%s retry=%s reason=%s delay=%s",
            result.effect_type,
            result.effect_ref,
            decision.should_retry,
            decision.reason,
            decision.delay_seconds,
        )
