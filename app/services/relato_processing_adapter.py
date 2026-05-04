# app/services/relato_processing_adapter.py

import logging
from concurrent.futures import ThreadPoolExecutor

from app.jobs.enrich_metadata_job import EnrichMetadataJob
from app.repositories.relato_repository import RelatoRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository

logger = logging.getLogger(__name__)


# pool global de workers
_executor = ThreadPoolExecutor(max_workers=2)


def _run_enrich_job(relato_id: str) -> None:
    """
    Executa o job real de enriquecimento.

    Esta funo roda dentro de uma thread worker.
    """
    logger.info("[relato_worker] iniciando processamento relato_id=%s", relato_id)

    try:
        job = EnrichMetadataJob(
            relato_repo=RelatoRepository(),
            effect_repo=EffectResultRepository(),
            enriched_repo=EnrichedMetadataRepository(),
        )

        job.run(relato_id)

        logger.info(
            "[relato_worker] processamento concludo relato_id=%s",
            relato_id,
        )

    except Exception as e:
        logger.exception(
            "[relato_worker] erro no processamento relato_id=%s erro=%s",
            relato_id,
            str(e),
        )


def enqueue_relato_processing(relato_id: str) -> None:
    """
    Adapter tcnico de processamento assncrono do relato.

    Evoluo arquitetural planejada:

    MVP:
        ThreadPoolExecutor

    Futuro:
        Cloud Tasks / PubSub / Worker service
    """

    logger.info("[enqueue_relato_processing] relato_id=%s", relato_id)

    # agenda execuo assncrona
    _executor.submit(_run_enrich_job, relato_id)
