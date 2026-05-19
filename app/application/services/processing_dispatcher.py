#app/application/services/processing_dispatcher.py

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.application.effects.dispatcher import EffectDispatcher
from app.application.relatos.mark_processed_use_case import MarkRelatoAsProcessedUseCase
from app.infra.event_adapter import DummyEventAdapter
from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository
from app.jobs.enrich_metadata_job import EnrichMetadataJob
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository
from app.repositories.relato_repository import RelatoRepository

logger = logging.getLogger(__name__)

# pool global de workers
_executor = ThreadPoolExecutor(max_workers=2)

def _on_job_completed(relato_id: str) -> None:
    """
    Callback chamado pelo job sincrono para iniciar a transicao de dominio assincrona.
    """
    logger.info("[relato_worker] disparando transicao de dominio para PROCESSED relato_id=%s", relato_id)

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        from app.infra.processing_adapter import CloudTasksProcessingAdapter

        repo = FirestoreRelatoRepository()
        dispatcher = EffectDispatcher(
            relato_repo=repo,
            processing_port=CloudTasksProcessingAdapter(),
            event_port=DummyEventAdapter()
        )
        use_case = MarkRelatoAsProcessedUseCase(repo, dispatcher)

        loop.run_until_complete(use_case.execute(relato_id))
    except Exception as e:
        logger.error("[relato_worker] falha ao executar MarkRelatoAsProcessedUseCase: %s", e)
    finally:
        loop.close()

def _run_enrich_job(relato_id: str) -> None:
    """
    Executa o job real de enriquecimento (Síncrono).
    """
    logger.info("[relato_worker] iniciando processamento relato_id=%s", relato_id)

    try:
        job = EnrichMetadataJob(
            relato_repo=RelatoRepository(),
            effect_repo=EffectResultRepository(),
            enriched_repo=EnrichedMetadataRepository(),
            on_completed_callback=_on_job_completed
        )

        job.run(relato_id)
        
        logger.info(
            "[relato_worker] processamento concluído relato_id=%s",
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
