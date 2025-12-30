"""
Registro explícito dos executores de efeitos do sistema.

Este módulo deve ser importado UMA vez no startup.
"""

from app.services.effects.registry import register_effect_executor

from app.services.effects.executors.upload_image import execute_upload_image
from app.services.effects.executors.enqueue_processing import execute_enqueue_processing
from app.services.effects.executors.emit_domain_event import execute_emit_domain_event
from app.services.effects.executors.persist_relato import execute_persist_relato


def register_all_effect_executors() -> None:
    """
    Registra todos os executores de efeitos conhecidos pelo sistema.
    """

    register_effect_executor("UPLOAD_IMAGE", execute_upload_image)
    register_effect_executor("ENQUEUE_JOB", execute_enqueue_processing)
    register_effect_executor("EMIT_DOMAIN_EVENT", execute_emit_domain_event)
    register_effect_executor("PERSIST_RELATO", execute_persist_relato)
