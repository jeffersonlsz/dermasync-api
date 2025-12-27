"""
Routes para relatos (depoimentos de tratamento de dermatite atópica).

Este módulo implementa os endpoints para gerenciamento de relatos,
incluindo o novo suporte a multipart/form-data para envio de imagens.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, status, Depends, Query
from typing import Optional, List, Dict
from uuid import uuid4
import json
from datetime import datetime, timezone

from pydantic import ValidationError
from app.auth.dependencies import get_current_user
from app.auth.schemas import User
from app.schema.relato import RelatoCompletoInput, FormularioMeta, RelatoStatusOutput
from app.services.relatos_service import process_and_save_relato, get_relato_by_id
from app.services.imagens_service import salvar_imagem_from_base64


# Rota principal
router = APIRouter(prefix="/relatos", tags=["Relatos"])
logger = logging.getLogger(__name__)


from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
import json
import uuid
import logging
from typing import List, Optional

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

from app.domain.orchestrator import (
    RelatoIntentOrchestrator,
    Actor,
    ActorType,
    Intent,
    IntentContext,
)

from app.domain.relato_executor import RelatoIntentExecutor
from app.domain.relato_status import RelatoStatus

from app.firestore.persistencia import salvar_relato_firestore
from app.schema.relato_draft import RelatoDraftInput  # 👈 schema NOVO (draft)

router = APIRouter()
logger = logging.getLogger(__name__)


from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
import json
import uuid
import logging
from typing import List, Optional

from app.auth.dependencies import get_current_user
from app.auth.schemas import User



from app.domain.relato_executor import RelatoIntentExecutor
from app.domain.relato_status import RelatoStatus
from app.schema.relato_draft import RelatoDraftInput
from app.firestore.persistencia import salvar_relato_firestore

router = APIRouter()
logger = logging.getLogger(__name__)


def parse_payload_json(payload: str) -> RelatoDraftInput:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload não é um JSON válido",
        )

    try:
        return RelatoDraftInput(**data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/relatos/enviar-relato-completo",
    status_code=status.HTTP_201_CREATED,
)
async def enviar_relato_completo(
    *,
    payload: str = Form(...),
    imagens_antes: Optional[List[UploadFile]] = File(default=None),
    imagens_durante: Optional[List[UploadFile]] = File(default=None),
    imagens_depois: Optional[List[UploadFile]] = File(default=None),
    current_user: User = Depends(get_current_user),
):
    logger.info(
        "[HTTP] /enviar-relato-completo | user=%s",
        current_user.id,
    )

    # =========================
    # 1️⃣ Parse do payload (draft)
    # =========================
    draft = parse_payload_json(payload)

    if not draft.consentimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consentimento é obrigatório",
        )

    # =========================
    # 2️⃣ Contexto inicial
    # =========================
    relato_id = uuid.uuid4().hex

    actor = Actor(
        type=ActorType.USER,
        id=current_user.id,
    )

    orchestrator = RelatoIntentOrchestrator()
    executor = RelatoIntentExecutor()

    # =========================
    # 3️⃣ CREATE_RELATO
    # =========================
    create_context = IntentContext(
        relato_id=relato_id,
        relato_exists=False,
        current_status=None,
        owner_id=None,
        payload=draft.model_dump(),
    )

    create_result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.CREATE_RELATO,
        context=create_context,
    )

    if not create_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_result.reason or "Criação não permitida",
        )

    # Persistência inicial (único ponto fora do executor, por enquanto)
    salvar_relato_firestore(
        relato_id=relato_id,
        owner_id=current_user.id,
        payload=draft.model_dump(),
        status=RelatoStatus.DRAFT.value,
    )

    # =========================
    # 4️⃣ ENVIAR_RELATO
    # =========================
    enviar_context = IntentContext(
        relato_id=relato_id,
        relato_exists=True,
        current_status=RelatoStatus.DRAFT,
        owner_id=current_user.id,
        payload=draft.model_dump(),
    )

    enviar_result = orchestrator.attempt_intent(
        actor=actor,
        intent=Intent.ENVIAR_RELATO,
        context=enviar_context,
    )

    if not enviar_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=enviar_result.reason or "Envio não permitido",
        )

    # =========================
    # 5️⃣ UPLOAD_IMAGES (efeito colateral)
    # =========================
    upload_context = IntentContext(
        relato_id=relato_id,
        relato_exists=True,
        current_status=RelatoStatus.UPLOADING,
        owner_id=current_user.id,
        payload=None,
    )

    executor.execute(
        intent=Intent.UPLOAD_IMAGES,
        context=upload_context,
        actor_id=current_user.id,
        payload={
            "imagens_antes": imagens_antes or [],
            "imagens_durante": imagens_durante or [],
            "imagens_depois": imagens_depois or [],
        },
    )

    # =========================
    # 6️⃣ Resposta
    # =========================
    return {
        "relato_id": relato_id,
        "status": enviar_result.new_status.value,
    }







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
    
    # Acessa os campos usando notação de ponto, pois 'relato' é um objeto Pydantic
    status = relato.status
    
    # Acesso seguro ao campo aninhado 'progress'
    progress = None
    if relato.processing and isinstance(relato.processing, dict):
        progress = relato.processing.get("progress")

    last_error = relato.last_error

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
    
# Rota pública para a galeria — devolve apenas campos seguros - será usado apenas por admin 
@router.get(
    "/admin/galeria/preview",
    summary="Preview administrativo de relatos",
    tags=["Admin"]
)
async def listar_relatos_preview_admin(
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Proteção por papel
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )

    from app.services.relatos_service import listar_relatos_publicos_preview

    relatos = await listar_relatos_publicos_preview(
        limit=limit,
        status_filter=status_filter
    )

    return {
        "quantidade": len(relatos),
        "dados": relatos
    }


@router.get(
    "/galeria/public",
    response_model=dict,
    summary="Galeria pública anonimizadas",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1)
):
    from app.services.relatos_service import listar_relatos_publicos_galeria_publica_preview

    relatos = await listar_relatos_publicos_galeria_publica_preview(
        limit=limit,
        page=page,
        only_public=True
    )

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(relatos)
        },
        "dados": relatos
    }
@router.get(
    "/galeria/public/v2",
    response_model=dict,
    summary="Galeria pública anonimizadas (v2)",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica_v2(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1)
):
    logger.info(f"Iniciando listagem galeria v2. Limit={limit}, Page={page}")
    from app.services.relatos_service import listar_relatos_publicos_galeria_publica_preview

    relatos = await listar_relatos_publicos_galeria_publica_preview(
        limit=limit,
        page=page,
        only_public=True
    )

    logger.info(f"Retornando {len(relatos)} relatos na galeria v2.")

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(relatos)
        },
        "dados": relatos
    }
from app.auth.dependencies import get_optional_user
@router.get(
    "/{relato_id}/imagens",
    summary="Imagens associadas ao relato (contrato canônico)",
    tags=["Relatos"]
)
async def get_imagens_relato(
    relato_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Endpoint canônico para consumo de imagens pelo front-end.
    """

    from app.services.imagens_service import get_imagens_por_relato

    # Por enquanto:
    # público e autenticado veem a mesma coisa
    include_private = False

    imagens = await get_imagens_por_relato(
        relato_id=relato_id,
        include_private=include_private
    )

    return imagens

@router.get(
    "/galeria/public/v3",
    summary="Galeria pública otimizada com thumbnails",
    tags=["Galeria Pública"]
)
async def listar_galeria_publica_v3(
    limit: int = Query(12, ge=1, le=24),
    page: int = Query(1, ge=1),
):
    from app.services.galeria_service import listar_galeria_publica_v3

    return await listar_galeria_publica_v3(
        limit=limit,
        page=page
    )
