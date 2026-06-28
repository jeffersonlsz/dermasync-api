import logging

from app.application.pipeline.constants import TASK_ENRICH_METADATA
from app.application.pipeline.manager import PipelineManager
from app.ports.processing_port import ProcessingPort
from app.repositories.relato_repository import RelatoRepository

logger = logging.getLogger(__name__)


class ReprocessAllRelatosUseCase:
    """
    Reenfileira todos os relatos para novo enriquecimento.
    """

    def __init__(
        self,
        pipeline_manager: PipelineManager,
        processing_port: ProcessingPort,
        relato_repo: RelatoRepository,
    ):
        self.pipeline_manager = pipeline_manager
        self.processing_port = processing_port
        self.relato_repo = relato_repo

    async def execute(self) -> dict:
        logger.info(
            "[ReprocessAllRelatosUseCase] iniciando reprocessamento global"
        )

        relatos = self.relato_repo.get_all()

        queued = 0

        for relato in relatos:
            relato_id = relato.get("id")

            if not relato_id:
                continue

            try:
                self.pipeline_manager.requeue_task(
                    relato_id=relato_id,
                    task_name=TASK_ENRICH_METADATA,
                )

                await self.processing_port.enqueue_relato_processing(
                    relato_id
                )

                queued += 1

            except Exception:
                logger.exception(
                    "[ReprocessAllRelatosUseCase] erro ao reenfileirar relato=%s",
                    relato_id,
                )

        logger.info(
            "[ReprocessAllRelatosUseCase] finalizado | queued=%s",
            queued,
        )

        return {
            "status": "queued",
            "task": TASK_ENRICH_METADATA,
            "queued": queued,
        }