import logging

from app.application.pipeline.constants import TASK_ENRICH_METADATA
from app.application.pipeline.manager import PipelineManager
from app.ports.processing_port import ProcessingPort
from app.repositories.relato_repository import RelatoRepository

logger = logging.getLogger(__name__)


class ReprocessRelatoUseCase:
    """
    Força o reprocessamento de uma tarefa do pipeline.

    Regras:
    - O relato precisa existir.
    - O estado atual da tarefa é ignorado.
    - A tarefa é recolocada em RETRY e reenfileirada.
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

    async def execute(self, relato_id: str) -> dict:
        logger.info(
            "[ReprocessRelatoUseCase] iniciando reprocessamento | relato_id=%s",
            relato_id,
        )

        relato = self.relato_repo.get_by_id(relato_id)

        if not relato:
            logger.warning(
                "[ReprocessRelatoUseCase] relato não encontrado | relato_id=%s",
                relato_id,
            )

            raise ValueError(
                f"Relato '{relato_id}' não encontrado."
            )

        self.pipeline_manager.requeue_task(
            relato_id=relato_id,
            task_name=TASK_ENRICH_METADATA,
        )

        await self.processing_port.enqueue_relato_processing(
            relato_id
        )

        logger.info(
            "[ReprocessRelatoUseCase] relato reenfileirado | relato_id=%s",
            relato_id,
        )

        return {
            "status": "queued",
            "relato_id": relato_id,
            "task": TASK_ENRICH_METADATA,
        }