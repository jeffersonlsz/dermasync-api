import logging
from app.application.services.processing_dispatcher import enqueue_relato_processing
from app.ports.processing_port import ProcessingPort


logger = logging.getLogger(__name__)

class CloudTasksProcessingAdapter(ProcessingPort):
    async def enqueue_relato_processing(self, relato_id: str) -> None:
        logger.info("INFRA: Enfileirando processamento para relato %s via Adapter", relato_id)
        # Reusa a lógica existente no service que já lida com o detalhe técnico
        enqueue_relato_processing(relato_id)
