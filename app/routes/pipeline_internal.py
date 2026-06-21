import logging
from fastapi import APIRouter, Depends, HTTPException
from app.application.pipeline.recovery_service import PipelineRecoveryService
from app.application.pipeline.manager import PipelineManager
from app.infra.adapters.thread_processing_adapter import enqueue_relato_processing
from app.ports.processing_port import ProcessingPort
from app.repositories.relato_repository import RelatoRepository
from app.auth.dependencies import get_current_user

from app.application.pipeline.reprocess_relato_use_case import (
    ReprocessRelatoUseCase,
)
from app.application.pipeline.constants import TASK_ENRICH_METADATA

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

def get_reprocess_use_case():
    manager = PipelineManager()
    repo = RelatoRepository()
    port = ThreadProcessingPort()
      

    return ReprocessRelatoUseCase(
        pipeline_manager=manager,
        processing_port=port,
        relato_repo=repo,
    )
    
@router.post("/reprocess/{relato_id}")
async def reprocess_relato(
    relato_id: str,
    use_case: ReprocessRelatoUseCase = Depends(
        get_reprocess_use_case
    ),
):
    """
    Força um novo enriquecimento de metadados
    para um relato específico.
    """

    try:
        result = await use_case.execute(relato_id)

        return {
            "status": "success",
            "data": result,
        }

    except Exception as e:
        logger.exception(
            "Erro ao reprocessar relato %s",
            relato_id,
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )