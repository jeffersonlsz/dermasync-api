import logging
from typing import List
from app.application.pipeline.manager import PipelineManager
from app.application.pipeline.constants import TASK_ENRICH_METADATA
from app.ports.processing_port import ProcessingPort

logger = logging.getLogger(__name__)

class PipelineRecoveryService:
    """
    Serviço responsável por identificar e recuperar tarefas que morreram no meio do caminho.
    """

    def __init__(self, pipeline_manager: PipelineManager, processing_port: ProcessingPort):
        self.pipeline_manager = pipeline_manager
        self.processing_port = processing_port

    async def recover_stuck_tasks(self, task_names: List[str] | None = None) -> dict:
        """
        Varre as tarefas conhecidas em busca de leases expirados e as re-enfileira.
        """
        if task_names is None:
            task_names = [TASK_ENRICH_METADATA]

        results = {}

        for task_name in task_names:
            logger.info(f"Iniciando recuperação de órfãos para a tarefa: {task_name}")
            orphan_ids = await self.pipeline_manager.find_orphans(task_name)
            
            recovered_count = 0
            for relato_id in orphan_ids:
                try:
                    # 1. Reseta o estado no Firestore (PROCESSING -> RETRY)
                    await self.pipeline_manager.reset_orphan(relato_id, task_name)
                    
                    # 2. Re-enfileira para processamento (BackgroundTasks / ThreadPool)
                    await self.processing_port.enqueue_relato_processing(relato_id)
                    
                    recovered_count += 1
                except Exception as e:
                    logger.error(f"Falha ao recuperar relato {relato_id} para a tarefa {task_name}: {e}")

            results[task_name] = recovered_count
            logger.info(f"Recuperação finalizada para {task_name}. Total recuperado: {recovered_count}")

        return results
