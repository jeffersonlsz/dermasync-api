"""
Routes para relatos (depoimentos de tratamento de dermatite atópica).

Este módulo implementa os endpoints para gerenciamento de relatos,
incluindo o novo suporte a multipart/form-data para envio de imagens.
"""

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, status, Depends
from typing import Optional, List, Dict
from uuid import uuid4
import json
from datetime import datetime, timezone

from app.auth.dependencies import get_current_user
from app.auth.schemas import User
from app.schema.relato import RelatoCompletoInput, FormularioMeta, RelatoStatusOutput
from app.services.relatos_service import process_and_save_relato, get_relato_by_id
from app.services.imagens_service import salvar_imagem_from_base64


# Rota principal
router = APIRouter(prefix="/relatos", tags=["Relatos"])


@router.post("/enviar-relato-completo", status_code=status.HTTP_201_CREATED)
async def enviar_relato_completo_multipart(
    background_tasks: BackgroundTasks,
    payload: str = Form(...),
    imagens_antes: list[UploadFile] = File([]),
    imagens_durante: list[UploadFile] = File([]),
    imagens_depois: list[UploadFile] = File([]),
    current_user: User = Depends(get_current_user),
):
    """
    Nova versão: aceita multipart/form-data (payload JSON + arquivos).
    Cria documento inicial e delega upload de arquivos + processamento a background tasks.
    """
    # 1) Parse e validação do payload
    try:
        data = json.loads(payload)
        meta = FormularioMeta(**data)
        if not meta.consentimento:
            raise ValueError("Consentimento obrigatório")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Payload inválido: {str(e)}")

    # 2) Validar limites de arquivos
    if len(imagens_antes) > 6 or len(imagens_durante) > 6 or len(imagens_depois) > 6:
        raise HTTPException(status_code=400, detail="Número máximo de imagens por categoria excedido (máximo: 6)")

    # 3) Validar tipo e tamanho dos arquivos
    from app.services.imagens_service import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_MB
    for file_list in [imagens_antes, imagens_durante, imagens_depois]:
        for upload_file in file_list:
            if upload_file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=415,
                    detail=f"Tipo de arquivo não suportado: {upload_file.content_type}. Permitidos: {', '.join(ALLOWED_MIME_TYPES)}"
                )
            # Check file size (for this we need to get the content, but avoid reading it multiple times)
            # We'll validate in the background processing as well

    # 4) Gerar ID do relato e documento inicial
    relato_id = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    initial_doc = {
        "id": relato_id,
        "owner_id": current_user.id,
        "meta": meta.dict(),
        "status": "uploading",
        "created_at": now,
        "images": {"antes": [], "durante": [], "depois": []},
        "processing": {"progress": 0}
    }

    # 5) Salvar documento inicial usando a persistência existente
    from app.firestore.persistencia import salvar_relato_firestore
    await salvar_relato_firestore(initial_doc, collection="relatos")

    # 6) Delegar salvamento dos arquivos e enfileiramento (função real no background service)
    from app.services.relatos_background import _save_files_and_enqueue
    background_tasks.add_task(
        _save_files_and_enqueue,
        relato_id,
        current_user.id,
        imagens_antes,
        imagens_durante,
        imagens_depois
    )

    return {"relato_id": relato_id, "status": "upload_received"}


# Rota antiga mantida para compatibilidade
@router.post("/completo", status_code=status.HTTP_201_CREATED)
async def enviar_relato_completo_json(
    relato: RelatoCompletoInput,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint antigo mantido para compatibilidade - aceita RelatoCompletoInput com base64.
    """
    result = await process_and_save_relato(relato, current_user)
    return result


@router.get("/{relato_id}/status", response_model=RelatoStatusOutput)
async def relato_status(
    relato_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para verificar o status de processamento de um relato.
    """
    relato = await get_relato_by_id(relato_id=relato_id, requesting_user=current_user)
    status = relato.get("status", "unknown")
    progress = relato.get("processing", {}).get("progress")
    last_error = relato.get("last_error")
    return {
        "relato_id": relato_id,
        "status": status,
        "progress": progress,
        "last_error": last_error
    }


@router.get("/{relato_id}")
async def get_relato(
    relato_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obter um relato pelo ID.
    """
    relato = await get_relato_by_id(relato_id=relato_id, requesting_user=current_user)
    return relato


@router.get("/listar-todos")
async def listar_relatos_wrapper(current_user: User = Depends(get_current_user)):
    """
    Endpoint para listar relatos (acesso controlado).
    """
    from app.services.relatos_service import listar_relatos
    
    # Apenas administradores e colaboradores podem listar todos
    if current_user.role not in ["admin", "colaborador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores e colaboradores podem listar todos os relatos."
        )
    
    relatos = await listar_relatos()
    return {"quantidade": len(relatos), "dados": relatos}


@router.get("/similares/{relato_id}")
async def get_relatos_similares(
    relato_id: str,
    top_k: int = 6,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para buscar relatos similares semanticamente.
    """
    # Este endpoint ainda precisa ser implementado completamente
    # Deixando como placeholder para implementação futura
    raise HTTPException(
        status_code=501,
        detail="Busca de relatos similares ainda não implementada."
    )