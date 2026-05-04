"""
Module commands.py.
"""

import logging
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException

from app.auth.schemas import User
from app.schema.relato import RelatoFullOutput, RelatoCompletoInput
from app.firestore.client import get_firestore_client
from app.services.imagens_service import get_imagem_by_id
from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, CreateRelato
from app.services.relato_effect_executor import RelatoEffectExecutor
from app.services.relato_adapters import (
    persist_relato_adapter,
    enqueue_processing_adapter,
    emit_event_adapter,
    upload_images_adapter,
    update_relato_status_adapter,
)

from app.services.relatos.mappers import map_relato_data

logger = logging.getLogger(__name__)

async def enqueue_relato_processing(relato_id: str) -> None:
    logger.info(f"Relato {relato_id} enfileirado para processamento em segundo plano.")
    pass

async def attach_image_to_relato(relato_id: str, image_id: str, current_user: User) -> RelatoFullOutput:
    db = get_firestore_client()
    if not db:
        logger.error("Erro ao obter o cliente Firestore")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

    doc_ref = db.collection("relatos").document(relato_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Relato no encontrado.")
    
    raw_data = doc.to_dict()
    mapped_data = map_relato_data(raw_data, doc.id)
    
    is_owner = mapped_data["owner_id"] == str(current_user.id)
    is_admin_or_colab = current_user.role in ["admin", "colaborador"]

    if not (is_owner or is_admin_or_colab):
        raise HTTPException(status_code=403, detail="Acesso negado. Voc no tem permisso para modificar este relato.")

    try:
        image_metadata = await get_imagem_by_id(image_id=image_id, requesting_user=current_user)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Imagem no encontrada ou no pertence a voc.")
        if e.status_code == 403:
            raise HTTPException(status_code=403, detail="Acesso negado à imagem.")
        raise e

    if image_metadata.get("status") in ["associated", "approved_public", "rejected", "archived"]:
        raise HTTPException(status_code=400, detail="Imagem j associada ou em estado final.")

    image_refs = mapped_data["image_refs"]
    if not image_refs:
        image_refs = {"antes": None, "durante": [], "depois": None}
    
    if image_id not in image_refs.get("durante", []):
        if "durante" not in image_refs:
            image_refs["durante"] = []
        image_refs["durante"].append(image_id)
    
    try:
        await doc_ref.update({"imagens_ids": image_refs, "updated_at": datetime.now(timezone.utc)})
        logger.info(f"Imagem {image_id} anexada ao relato {relato_id}.")
        
        image_doc_ref = db.collection("imagens").document(image_id)
        await image_doc_ref.update({"status": "associated", "updated_at": datetime.now(timezone.utc)})
        
        mapped_data["image_refs"] = image_refs
        return RelatoFullOutput(**mapped_data)
    except Exception as e:
        logger.exception(f"Falha ao anexar imagem {image_id} ao relato {relato_id}.")
        raise HTTPException(status_code=500, detail=f"Erro ao anexar imagem: {str(e)}")

async def process_and_save_relato(relato: RelatoCompletoInput, current_user: User) -> dict:
    if not relato.conteudo_original.strip():
        raise HTTPException(status_code=400, detail="Relato no pode estar vazio.")

    relato_id = uuid.uuid4().hex
    command = CreateRelato(
        relato_id=relato_id,
        owner_id=current_user.id,
        conteudo=relato.conteudo_original,
        imagens={
            "antes": relato.imagens.antes,
            "durante": relato.imagens.durante,
            "depois": relato.imagens.depois,
        },
    )

    actor = Actor(
        id=current_user.id,
        role=current_user.role,
    )

    decision = decide(command=command, actor=actor, current_state=None)

    if not decision.allowed:
        raise HTTPException(status_code=400, detail=decision.reason)

    executor = RelatoEffectExecutor(
        persist_relato=persist_relato_adapter,
        enqueue_processing=enqueue_processing_adapter,
        emit_event=emit_event_adapter,
        upload_images=upload_images_adapter,
        update_relato_status=update_relato_status_adapter,
    )

    executor.execute(effects=decision.effects)

    return {
        "status": "sucesso",
        "message": "Relato recebido com sucesso.",
        "relato_id": relato_id,
    }

def run_submission_effects(effects: list, executor: RelatoEffectExecutor) -> None:
    try:
        executor.execute(effects)
    except Exception as e:
        logger.error(f"Erro ao executar efeitos da submisso em background: {e}", exc_info=True)
