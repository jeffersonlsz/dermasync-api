# app/services/relato_adapters.py
import logging

logger = logging.getLogger(__name__)

def persist_relato_adapter(relato_id: str, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Persistindo relato {relato_id} com {args} e {kwargs}")

def enqueue_processing_adapter(relato_id: str, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Enfileirando processamento para {relato_id} com {args} e {kwargs}")

def emit_event_adapter(event_name: str, payload: dict, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Emitindo evento {event_name} com payload {payload}, {args} e {kwargs}")

def upload_images_adapter(relato_id: str, imagens: dict, *args, **kwargs):
    logger.info(f"DUMMY ADAPTER: Upload de imagens para {relato_id}: {imagens.keys()} com {args} e {kwargs}")
