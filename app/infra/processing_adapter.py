import logging
from app.ports.processing_port import ProcessingPort
from app.services.relato_processing_adapter import enqueue_relato_processing

logger = logging.getLogger(__name__)

class CloudTasksProcessingAdapter(ProcessingPort):
    async def enqueue_relato_processing(self, relato_id: str) -> None:
        logger.info("INFRA: Enfileirando processamento para relato %s via Adapter", relato_id)
        # Reusa a lógica existente no service que já lida com o detalhe técnico
        enqueue_relato_processing(relato_id)
