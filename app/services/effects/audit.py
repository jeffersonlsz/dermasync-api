"""
Module audit.py.
"""

import logging
from app.services.effects.build_result import build_effect_result
from app.services.effects.persist_firestore import persist_effect_result_firestore

logger = logging.getLogger(__name__)

def record_effect_result(relato_id: str, effect_type: str, effect_ref: str, success: bool, metadata: dict = None, error: str = None):
    try:
        result = build_effect_result(
            relato_id=relato_id,
            effect_type=effect_type,
            effect_ref=effect_ref,
            success=success,
            metadata=metadata,
            error=error,
        )
        persist_effect_result_firestore(result)
        return result
    except Exception as exc:
        logger.exception(f"Erro ao registrar auditoria do efeito {effect_type}: {exc}")
