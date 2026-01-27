# app/infra/retry/retry_scheduler.py
import logging
from typing import Iterable

from app.services.effects.result import EffectResult, EffectStatus
from app.services.effects.retry_engine import RetryEngine
from app.services.effects.persist_firestore import persist_effect_result_firestore
from app.services.relato_effect_executor import RelatoEffectExecutor

logger = logging.getLogger(__name__)


class RetryScheduler:
    """
    Orquestrador técnico de retries.
    NÃO conhece domínio.
    NÃO cria efeitos.
    """

    def __init__(
        self,
        *,
        load_failed_results,
        effect_executor: RelatoEffectExecutor,
        retry_engine: RetryEngine | None = None,
    ):
        self._load_failed_results = load_failed_results
        self._executor = effect_executor
        self._retry_engine = retry_engine or RetryEngine()

    def run_once(self) -> None:
        """
        Executa um ciclo de retry.
        Pode ser chamado por cron, job ou manualmente.
        """

        failed_results: Iterable[EffectResult] = self._load_failed_results()

        logger.info("RetryScheduler | falhas encontradas=%d", len(failed_results))

        for result in failed_results:

            enriched = self._retry_engine.decide(result)

            # Persistimos a decisão, SEMPRE
            persist_effect_result_firestore(enriched)

            if enriched.status == EffectStatus.RETRYING:
                logger.info(
                    "RetryScheduler | reexecutando effect=%s | attempt=%s",
                    enriched.effect_type,
                    enriched.metadata.get("attempt", 1) if enriched.metadata else 1,
                )

                attempt = enriched.metadata.get("attempt", 1)

                try:
                    self._executor.execute_by_result(
                        effect_result=enriched,
                        attempt=attempt,
                    )

                except Exception:
                    logger.exception(
                        "RetryScheduler | falha ao reexecutar efeito | effect=%s",
                        enriched.effect_type,
                    )
            else: # enriched.status == EffectStatus.ERROR (or SUCCESS, but that shouldn't happen here)
                logger.info(
                    "RetryScheduler | abortando retry | effect=%s | reason=%s",
                    enriched.effect_type,
                    enriched.metadata.get("failure_type", "no-retry-decision"),
                )
