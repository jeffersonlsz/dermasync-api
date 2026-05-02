# app/services/mock_relato_adapters.py
import logging

logger = logging.getLogger(__name__)


def mock_persist_relato(relato_id: str):
    logger.info(
        "[MOCK] PersistRelatoEffect executado | relato_id=%s",
        relato_id,
    )


def mock_enqueue_processing(relato_id: str):
    logger.info(
        "[MOCK] EnqueueProcessingEffect executado | relato_id=%s",
        relato_id,
    )


def mock_emit_event(event_name: str, payload: dict | None):
    logger.info(
        "[MOCK] EmitDomainEventEffect | event=%s payload=%s",
        event_name,
        payload,
    )
