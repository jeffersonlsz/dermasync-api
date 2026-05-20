# app/services/relato_processing_adapter.py

import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.jobs.enrich_metadata_job import EnrichMetadataJob
from app.repositories.relato_repository import RelatoRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository

# Imports para transição de domínio
from app.infra.firestore.relato_repository_impl import FirestoreRelatoRepository
from app.infra.processing_adapter import CloudTasksProcessingAdapter
from app.infra.event_adapter import DummyEventAdapter
from app.application.effects.dispatcher import EffectDispatcher
from app.application.relatos.mark_processed_use_case import MarkRelatoAsProcessedUseCase

logger = logging.getLogger(__name__)


# pool global de workers
_executor = ThreadPoolExecutor(max_workers=2)

def _on_job_completed(relato_id: str) -> None:
    """
    Callback chamado pelo Job síncrono para iniciar a transição de domínio assíncrona.
    """
    logger.info("[relato_worker] disparando transição de domínio para PROCESSED relato_id=%s", relato_id)
    
    # Cria os componentes necessários para o Use Case
    # Como estamos em uma thread do pool, precisamos de um novo loop ou usar o existente
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        repo = FirestoreRelatoRepository()
        dispatcher = EffectDispatcher(
            relato_repo=repo,
            processing_port=CloudTasksProcessingAdapter(),
            event_port=DummyEventAdapter()
        )
        use_case = MarkRelatoAsProcessedUseCase(repo, dispatcher)
        
        loop.run_until_complete(use_case.execute(relato_id))
        loop.close()
    except Exception as e:
        logger.error(f"[relato_worker] falha ao executar MarkRelatoAsProcessedUseCase: {e}")


def enqueue_relato_processing(relato_id: str) -> None:
    """
    Compatibilidade para imports legados do adapter de thread.

    A implementacao ativa do enfileiramento vive em
    app.application.services.processing_dispatcher. Este wrapper preserva o
    contrato publico esperado por rotas e executores de effects.
    """
    from app.application.services.processing_dispatcher import (
        enqueue_relato_processing as dispatch_processing,
    )

    dispatch_processing(relato_id)





