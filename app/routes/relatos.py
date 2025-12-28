"""
Routes para relatos (depoimentos de tratamento de dermatite atópica).

Este módulo implementa os endpoints para gerenciamento de relatos,
incluindo o novo suporte a multipart/form-data para envio de imagens.
"""

from fastapi import APIRouter, Depends, Form, File, Query, UploadFile, HTTPException, status
from typing import Optional, List
import uuid
import logging
import json

from app.auth.dependencies import get_current_user
from app.auth.schemas import User

from app.domain.orchestrator import ActorType, Intent, IntentContext
from app.domain.relato.orchestrator import RelatoIntentOrchestrator
from app.domain.relato.contracts import Actor, RelatoContext
from app.domain.relato.intents import RelatoIntent
from app.domain.relato.states import RelatoStatus

from app.domain.relato_executor import RelatoIntentExecutor
from app.firestore.persistencia import salvar_relato_firestore
from app.schema.relato import RelatoCompletoInput, RelatoStatusOutput
from app.services.relato_effect_executor import RelatoEffectExecutor
from app.schema.relato_draft import RelatoDraftInput
from app.services.mock_relato_adapters import (
    mock_persist_relato,
    mock_enqueue_processing,
    mock_emit_event,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def parse_payload_json(payload: str) -> RelatoDraftInput:
    try:
        data = json.loads(payload)
        return RelatoDraftInput(**data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/relatos",
    status_code=status.HTTP_201_CREATED,
    summary="Enviar relato (rota canônica baseada em domínio)",
)
async def criar_e_enviar_relato(
    *,
    payload: str = Form(...),
    imagens_antes: Optional[List[UploadFile]] = File(default=None),
    imagens_durante: Optional[List[UploadFile]] = File(default=None),
    imagens_depois: Optional[List[UploadFile]] = File(default=None),
    current_user: User = Depends(get_current_user),
):
    logger.info("[HTTP] POST /relatos | user=%s", current_user.id)

    # ============================================================
    # 1️⃣ Parse e validação mínima do payload (fora do domínio)
    # ============================================================
    draft = parse_payload_json(payload)

    if not draft.consentimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consentimento é obrigatório",
        )

    relato_id = uuid.uuid4().hex

    # ============================================================
    # 2️⃣ Preparação do domínio
    # ============================================================
    actor = Actor(
        id=current_user.id,
        role="user",
    )

    orchestrator = RelatoIntentOrchestrator()

    executor = RelatoEffectExecutor(
        persist_relato=mock_persist_relato,          # MOCK
        enqueue_processing=mock_enqueue_processing,  # MOCK
        emit_event=mock_emit_event,                  # MOCK
    )

    # ============================================================
    # 3️⃣ Intent 1 — CREATE_RELATO
    # ============================================================
    create_context = RelatoContext(
        relato_id=relato_id,
        relato_exists=False,
        current_state=None,
        owner_id=current_user.id,
        payload=draft.model_dump(),
    )

    create_decision = orchestrator.attempt(
        actor=actor,
        intent=RelatoIntent.CREATE_RELATO,
        context=create_context,
    )

    if not create_decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_decision.reason or "Criação do relato não permitida",
        )

    # Executa efeitos da criação (ex: persistir DRAFT)
    executor.execute(create_decision.effects)

    # ============================================================
    # 4️⃣ Intent 2 — ENVIAR_RELATO
    # ============================================================
    enviar_context = RelatoContext(
        relato_id=relato_id,
        relato_exists=True,
        current_state=RelatoStatus.DRAFT,
        owner_id=current_user.id,
        payload=draft.model_dump(),
    )

    enviar_decision = orchestrator.attempt(
        actor=actor,
        intent=RelatoIntent.ENVIAR_RELATO,
        context=enviar_context,
    )

    if not enviar_decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=enviar_decision.reason or "Envio do relato não permitido",
        )

    # Executa efeitos do envio (ex: enfileirar processamento)
    executor.execute(enviar_decision.effects)

    # ============================================================
    # 5️⃣ Resposta HTTP (nenhuma lógica aqui)
    # ============================================================
    return {
        "relato_id": relato_id,
        "status": enviar_decision.next_state.value,
    }




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
