import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from google.cloud import firestore
from app.firestore.client import get_firestore_client
from app.application.pipeline.enums import EffectExecutionState

logger = logging.getLogger(__name__)

class PipelineManager:
    """
    Gerencia o estado operacional (Lease Pattern) das tarefas no Firestore.
    Versão síncrona para compatibilidade com ThreadPoolExecutor.
    """

    def __init__(self, collection_name: str = "relatos"):
        self.db = get_firestore_client()
        self.collection = self.db.collection(collection_name)

    def claim_task(
        self, 
        relato_id: str, 
        task_name: str, 
        worker_id: str, 
        lease_duration_minutes: int = 5
    ) -> bool:
        """
        Tenta 'reclamar' uma tarefa de forma atômica (Síncrono).
        """
        doc_ref = self.collection.document(relato_id)
        
        @firestore.transactional
        def _claim_transaction(transaction, doc_ref):
            snapshot = doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                logger.warning(f"[PipelineManager] Claim negado: Relato {relato_id} não encontrado.")
                return False

            data = snapshot.to_dict()
            pipeline = data.get("_pipeline", {})
            tasks = pipeline.get("tasks", {})
            task_data = tasks.get(task_name)

            now = datetime.utcnow()

            if not task_data:
                logger.info(f"[PipelineManager] Tarefa {task_name} inicializada no relato {relato_id}.")
                is_available = True
                is_expired = False
                current_attempt = 0
            else:
                state = task_data.get("state")
                lease_expires_at = task_data.get("lease_expires_at")
                current_attempt = task_data.get("attempt", 0)

                is_available = state in [EffectExecutionState.PENDING, EffectExecutionState.RETRY]
                is_expired = state == EffectExecutionState.PROCESSING and lease_expires_at and lease_expires_at < now

                if not (is_available or is_expired):
                    return False

            new_attempt = current_attempt + 1
            new_lease_expiry = now + timedelta(minutes=lease_duration_minutes)
            task_prefix = f"_pipeline.tasks.{task_name}"
            
            updates = {
                "_pipeline.active": True,
                f"{task_prefix}.state": EffectExecutionState.PROCESSING,
                f"{task_prefix}.attempt": new_attempt,
                f"{task_prefix}.worker_id": worker_id,
                f"{task_prefix}.lease_expires_at": new_lease_expiry,
                f"{task_prefix}.updated_at": now
            }
            
            transaction.update(doc_ref, updates)
            return True

        transaction = self.db.transaction()
        try:
            return _claim_transaction(transaction, doc_ref)
        except Exception as e:
            logger.error(f"Erro no claim_task: {e}")
            return False

    def complete_task(self, relato_id: str, task_name: str):
        doc_ref = self.collection.document(relato_id)
        task_prefix = f"_pipeline.tasks.{task_name}"
        doc_ref.update({
            f"{task_prefix}.state": EffectExecutionState.PROCESSED,
            f"{task_prefix}.lease_expires_at": None,
            f"{task_prefix}.updated_at": datetime.utcnow()
        })

    def fail_task(self, relato_id: str, task_name: str, error_message: str, max_attempts: int = 3):
        doc_ref = self.collection.document(relato_id)
        doc = doc_ref.get()
        if not doc.exists: return

        task_data = doc.to_dict().get("_pipeline", {}).get("tasks", {}).get(task_name, {})
        attempts = task_data.get("attempt", 0)
        new_state = EffectExecutionState.RETRY if attempts < max_attempts else EffectExecutionState.DEAD_LETTER

        task_prefix = f"_pipeline.tasks.{task_name}"
        doc_ref.update({
            f"{task_prefix}.state": new_state,
            f"{task_prefix}.last_error": error_message,
            f"{task_prefix}.lease_expires_at": None,
            f"{task_prefix}.updated_at": datetime.utcnow()
        })

    def find_orphans(self, task_name: str) -> list[str]:
        now = datetime.utcnow()
        query = self.collection.where(
            filter=firestore.FieldFilter(f"_pipeline.tasks.{task_name}.state", "==", EffectExecutionState.PROCESSING)
        ).where(
            filter=firestore.FieldFilter(f"_pipeline.tasks.{task_name}.lease_expires_at", "<", now)
        )
        return [doc.id for doc in query.stream()]

    def reset_orphan(self, relato_id: str, task_name: str):
        doc_ref = self.collection.document(relato_id)
        task_prefix = f"_pipeline.tasks.{task_name}"
        doc_ref.update({
            f"{task_prefix}.state": EffectExecutionState.RETRY,
            f"{task_prefix}.last_error": "Lease expired",
            f"{task_prefix}.lease_expires_at": None,
            f"{task_prefix}.updated_at": datetime.utcnow()
        })
