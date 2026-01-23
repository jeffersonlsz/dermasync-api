# app/services/relato_processing_adapter.py
import logging

from app.jobs.enrich_metadata_job import EnrichMetadataJob
from app.repositories.relato_repository import RelatoRepository
from app.repositories.effect_result_repository import EffectResultRepository
from app.repositories.enriched_metadata_repository import EnrichedMetadataRepository

logger = logging.getLogger(__name__)


def enqueue_relato_processing(relato_id: str) -> None:
    """
    Adapter técnico de processamento assíncrono do relato.

    Hoje: execução direta (thread / worker).
    Amanhã: Cloud Tasks / PubSub.
    """

    logger.info("[enqueue_relato_processing] relato_id=%s", relato_id)
    logger.debug("[enqueue_relato_processing] relato_id=%s", relato_id)

    # ⚠️ MVP: execução direta (assíncrona fora do request)
    job = EnrichMetadataJob(
        relato_repo=RelatoRepository(),
        effect_repo=EffectResultRepository(),
        enriched_repo=EnrichedMetadataRepository(),
    )

    # Aqui você pode:
    # - rodar em thread
    # - rodar em background task
    # - ou apenas chamar (se já estiver fora do request)
    job.run(relato_id)
