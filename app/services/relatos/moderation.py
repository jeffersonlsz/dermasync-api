"""
Module moderation.py.
"""

import logging
import asyncio
from fastapi import HTTPException

from app.auth.schemas import User
from app.firestore.client import get_firestore_client
from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, ApproveRelatoPublic, RejectRelato, ArchiveRelato
from app.domain.relato.states import RelatoStatus
from app.services.relato_effect_executor import RelatoEffectExecutor
from app.services.relato_adapters import update_relato_status_adapter

logger = logging.getLogger(__name__)

async def moderate_relato(relato_id: str, action: str, current_user: User) -> dict:
    db = get_firestore_client()
    doc_ref = db.collection("relatos").document(relato_id)
    doc = await asyncio.to_thread(doc_ref.get)

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Relato nÃ£o encontrado.")

    relato_data = doc.to_dict()
    current_status_str = relato_data.get("status")
    if not current_status_str:
        raise HTTPException(status_code=400, detail="Relato sem status definido.")
    
    current_status = RelatoStatus(current_status_str)

    command_map = {
        "approve": ApproveRelatoPublic(relato_id=relato_id),
        "reject": RejectRelato(relato_id=relato_id),
        "archive": ArchiveRelato(relato_id=relato_id),
    }

    command = command_map.get(action.lower())
    if not command:
        raise HTTPException(status_code=400, detail=f"AÃ§Ã£o de moderaÃ§Ã£o invÃ¡lida: '{action}'. VÃ¡lidas: approve, reject, archive.")

    actor = Actor(id=current_user.id, role=current_user.role)

    decision = decide(command=command, actor=actor, current_state=current_status)

    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    executor = RelatoEffectExecutor(
        persist_relato=lambda *args, **kwargs: None,
        enqueue_processing=lambda *args, **kwargs: None,
        emit_event=lambda *args, **kwargs: None,
        upload_images=lambda *args, **kwargs: None,
        update_relato_status=update_relato_status_adapter,
    )
    executor.execute(effects=decision.effects)

    return {
        "id": relato_id,
        "previous_status": current_status.value,
        "new_status": decision.next_state.value,
        "message": f"Relato {relato_id} teve seu status alterado para {decision.next_state.value}."
    }
