from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field
from app.application.pipeline.enums import EffectExecutionState

class EffectTaskTracker(BaseModel):
    """
    Rastreador de estado para um efeito específico (ex: ENRICH_METADATA).
    """
    state: EffectExecutionState = EffectExecutionState.PENDING
    attempt: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Campos para Fases 2+
    lease_expires_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    last_error: Optional[str] = None

class PipelineState(BaseModel):
    """
    Estado global do pipeline operacional de um relato.
    Persistido sob a chave '_pipeline' no Firestore.
    """
    active: bool = False
    tasks: Dict[str, EffectTaskTracker] = Field(default_factory=dict)
    
    @classmethod
    def create_initial(cls, task_names: list[str]) -> "PipelineState":
        """
        Cria um estado inicial com as tarefas marcadas como PENDING.
        """
        tasks = {
            name: EffectTaskTracker(state=EffectExecutionState.PENDING, attempt=0)
            for name in task_names
        }
        return cls(active=True, tasks=tasks)
