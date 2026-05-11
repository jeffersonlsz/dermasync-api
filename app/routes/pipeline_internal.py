import logging
from fastapi import APIRouter, Depends, HTTPException
from app.application.pipeline.recovery_service import PipelineRecoveryService
from app.application.pipeline.manager import PipelineManager
from app.infra.adapters.thread_processing_adapter import enqueue_relato_processing
from app.ports.processing_port import ProcessingPort

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/pipeline", tags=["Internal Pipeline"])

# Mock ProcessingPort for simplicity in the route
class ThreadProcessingPort(ProcessingPort):
    async def enqueue_relato_processing(self, relato_id: str) -> None:
        from app.infra.adapters.thread_processing_adapter import enqueue_relato_processing
        enqueue_relato_processing(relato_id)

def get_recovery_service():
    manager = PipelineManager()
    port = ThreadProcessingPort()
    return PipelineRecoveryService(manager, port)

@router.post("/recover")
async def recover_pipeline(service: PipelineRecoveryService = Depends(get_recovery_service)):
    """
    Endpoint manual para disparar a recuperação de tarefas órfãs (lease expirado).
    Pode ser chamado por um CronJob ou Cloud Scheduler.
    """
    try:
        results = await service.recover_stuck_tasks()
        return {
            "status": "success",
            "recovered": results
        }
    except Exception as e:
        logger.exception("Erro ao executar recuperação do pipeline")
        raise HTTPException(status_code=500, detail=str(e))
