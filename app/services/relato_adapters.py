# app/services/relato_adapters.py
import logging
from datetime import datetime, timezone
from app.firestore.client import get_firestore_client
from app.domain.relato.states import RelatoStatus

logger = logging.getLogger(__name__)

def persist_relato_adapter(relato_id: str, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Persistindo relato {relato_id} com {args} e {kwargs}")

def enqueue_processing_adapter(relato_id: str, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Enfileirando processamento para {relato_id} com {args} e {kwargs}")

def emit_event_adapter(event_name: str, payload: dict, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Emitindo evento {event_name} com payload {payload}, {args} e {kwargs}")

def upload_images_adapter(relato_id: str, imagens: dict, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Upload de imagens para {relato_id}: {imagens.keys()} com {args} e {kwargs}")

def update_relato_status_adapter(relato_id: str, new_status: RelatoStatus):
    """
    Adapter real para atualizar o status de um relato no Firestore.
    """
    logger.info(f"ADAPTER: Atualizando status do relato {relato_id} para {new_status.value}")
    db = get_firestore_client()
    doc_ref = db.collection("relatos").document(relato_id)
    doc_ref.update({"status": new_status.value, "updated_at": datetime.now(timezone.utc)})
    logger.info(f"ADAPTER: Status do relato {relato_id} atualizado com sucesso.")
